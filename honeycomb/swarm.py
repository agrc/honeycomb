#!/usr/bin/env python
# * coding: utf8 *
"""
swarm.py

A module that contains code for etl-ing tiles into WMTS format and uploading to GCP.
"""

import os
import traceback
from base64 import b64encode
from functools import partial
from multiprocessing.pool import ThreadPool
from pathlib import Path

import requests
from google.api_core.retry import Retry
from google_crc32c import Checksum
from PIL import Image

from . import config, settings
from .log import logger, logging_tqdm
from .messaging import send_email


def _empty_upload_summary():
    return {
        "created": 0,
        "updated": 0,
        "skipped_same_crc": 0,
        "converted": 0,
        "errors": 0,
        "logged_tiles": 0,
    }


def _merge_upload_summaries(summaries):
    totals = _empty_upload_summary()
    for summary in summaries:
        for key in totals:
            totals[key] += summary[key]

    return totals


def _format_upload_summary(title, context, summary):
    context_lines = [f"  {key}: {value}" for key, value in context.items()]
    summary_lines = [f"  {key}: {value}" for key, value in summary.items()]

    return "\n".join([title, *context_lines, *summary_lines])


def _format_cache_job_summary(bucket_name, name, level_summaries):
    totals = _empty_upload_summary()
    total_rows = 0
    lines = [
        "cache upload summary",
        f"  bucket: {bucket_name}",
        f"  prefix: {name}",
        "",
        "  level  rows  created  updated  skipped_same_crc  converted  errors  logged_tiles",
    ]

    for level, rows, summary in level_summaries:
        total_rows += rows
        for key in totals:
            totals[key] += summary[key]
        lines.append(
            "  {level:>5}  {rows:>4}  {created:>7}  {updated:>7}  {skipped_same_crc:>16}  {converted:>9}  {errors:>6}  {logged_tiles:>12}".format(
                level=level,
                rows=rows,
                **summary,
            )
        )

    lines.extend(
        [
            "",
            "  totals",
            f"    rows: {total_rows}",
            *[f"    {key}: {value}" for key, value in totals.items()],
        ]
    )

    return "\n".join(lines)


def swarm(name, bucket_name, image_type, is_test=False, preview_url=None):
    """
    copies all tiles into WMTS format as a sibling folder to the cache folder
    returns a list of all of the column folders
    """
    base_folder = Path(settings.CACHES_DIR) / f"{name}_Exploded" / "_alllayers"

    if is_test:
        bucket_name += "-test"

    # Temporary upload diagnostics toggles.
    diagnostics_enabled = True
    log_all_tiles = False

    if diagnostics_enabled:
        logger.info("upload diagnostics enabled")
    if log_all_tiles:
        logger.info("tile upload diagnostics enabled for all tiles")

    level_summaries = []

    for level_folder in sorted(base_folder.iterdir()):
        level = str(int(level_folder.name[1:]))
        logger.info("uploading level: {}".format(level))

        row_folders = [folder for folder in sorted(level_folder.iterdir())]
        if len(row_folders) > 0:
            with (
                ThreadPool(config.pool_threads) as pool,
                logging_tqdm(total=len(row_folders)) as progress_bar,
            ):
                summaries = pool.map(
                    partial(
                        process_row_folder,
                        name,
                        bucket_name,
                        level,
                        progress_bar,
                        image_type,
                        diagnostics_enabled,
                        log_all_tiles,
                    ),
                    row_folders,
                )
                totals = _merge_upload_summaries(summaries)
                level_summaries.append((level, len(row_folders), totals))

                if diagnostics_enabled:
                    logger.info(
                        _format_upload_summary(
                            "level upload summary",
                            {
                                "bucket": bucket_name,
                                "prefix": name,
                                "level": level,
                                "rows": len(row_folders),
                            },
                            totals,
                        )
                    )
            # with logging_tqdm(total=len(row_folders)) as progress_bar:
            #     map(partial(process_row_folder, name, bucket_name, level, progress_bar), row_folders)

    if diagnostics_enabled:
        logger.info(_format_cache_job_summary(bucket_name, name, level_summaries))

    bust_discover_cache()

    if is_test:
        send_email(
            "honeycomb update", f"{name}-Test is ready for review.\n\n{preview_url}"
        )
    else:
        send_email("honeycomb update", f"{name} has been pushed to production")


def convert_png_to_jpg(file_path) -> Path:
    """
    This function exists because I was unable to get the ManageTileCache tool in worker_bee.py
    to generate JPGs. No matter what tile cache scheme file I pointed it at, it stubbornly
    generated PNGs.
    """
    image = Image.open(file_path)
    bands = image.split()
    if len(bands) == 4:
        new_image = Image.new("RGB", image.size, (255, 255, 255))
        new_image.paste(image, mask=bands[3])  # 3 is the alpha channel
    else:
        #: handle PNGs with no alpha channel (blank white tiles)
        new_image = image.convert("RGB")
    new_file_path = file_path.with_suffix(".jpg")
    new_image.save(new_file_path, "JPEG", quality=75)
    file_path.unlink()

    return new_file_path


def process_row_folder(
    name,
    bucket_name,
    level,
    progress_bar,
    image_type,
    diagnostics_enabled,
    log_all_tiles,
    row_folder,
):
    retry = Retry()
    bucket = config.get_storage_client().bucket(bucket_name)
    row = str(int(row_folder.name[1:], 16))
    upload_errors = []
    summary = _empty_upload_summary()
    for file_path in row_folder.iterdir():
        column = "unknown"
        blob_name = "unknown"
        local_checksum = None
        remote_checksum = None
        action = "unknown"
        source_file_path = file_path
        converted = False
        try:
            column = str(int(file_path.name[1:-4], 16))
            #: set the content type explicitly in case it ever changes for a particular tile
            #: if you pass none then the content type of the existing blob object is used
            if file_path.suffix == ".png":
                if image_type and image_type.upper() == "JPEG":
                    file_path = convert_png_to_jpg(file_path)
                    content_type = "image/jpeg"
                    converted = True
                    summary["converted"] += 1
                else:
                    content_type = "image/png"
            else:
                content_type = "image/jpeg"

            blob_name = f"{name}/{level}/{column}/{row}"
            log_tile = log_all_tiles
            if log_tile:
                summary["logged_tiles"] += 1

            blob = bucket.blob(blob_name)
            if blob.exists(retry=retry):
                blob.reload()  #: required to get the checksum
                remote_checksum = blob.crc32c
                local_checksum = b64encode(
                    Checksum(file_path.read_bytes()).digest()
                ).decode("utf-8")
                if remote_checksum != local_checksum:
                    blob.upload_from_filename(
                        file_path, retry=retry, content_type=content_type
                    )
                    action = "updated"
                    summary["updated"] += 1
                else:
                    action = "skipped_same_crc"
                    summary["skipped_same_crc"] += 1
            else:
                if log_tile:
                    local_checksum = b64encode(
                        Checksum(file_path.read_bytes()).digest()
                    ).decode("utf-8")
                blob.upload_from_filename(
                    file_path, retry=retry, content_type=content_type
                )
                action = "created"
                summary["created"] += 1

            if log_tile:
                logger.info(
                    "tile upload decision: bucket=%s blob=%s action=%s remote_crc32c=%s local_crc32c=%s generation=%s metageneration=%s updated=%s size=%s content_type=%s converted=%s source=%s upload_file=%s",
                    bucket_name,
                    blob_name,
                    action,
                    remote_checksum,
                    local_checksum,
                    getattr(blob, "generation", None),
                    getattr(blob, "metageneration", None),
                    getattr(blob, "updated", None),
                    getattr(blob, "size", None),
                    content_type,
                    converted,
                    source_file_path,
                    file_path,
                )
            file_path.unlink()
        except Exception:
            summary["errors"] += 1
            trace = traceback.format_exc()
            upload_errors.append(
                f"Uploading error. Level: {level}, row: {row}, column: {column}\n\n{trace}"
            )
            if log_all_tiles:
                logger.error(
                    "tile upload decision failed: bucket=%s blob=%s action=%s remote_crc32c=%s local_crc32c=%s source=%s upload_file=%s",
                    bucket_name,
                    blob_name,
                    action,
                    remote_checksum,
                    local_checksum,
                    source_file_path,
                    file_path,
                )
            logger.error(trace)
    try:
        row_folder.rmdir()
    except Exception:
        trace = traceback.format_exc()
        logger.error(trace)

    progress_bar.update()

    return summary


def bust_discover_cache():
    logger.info("busting discover cache")
    giza_instance = config.get_config_value("gizaInstance")

    with requests.Session() as session:
        response = session.post(
            "{}/login".format(giza_instance),
            data={
                "user": os.getenv("HONEYCOMB_GIZA_USERNAME"),
                "password": os.getenv("HONEYCOMB_GIZA_PASSWORD"),
            },
        )

        if response.status_code != 200:
            raise Exception("Login failed")

        response = session.get("{}/reset".format(giza_instance))
