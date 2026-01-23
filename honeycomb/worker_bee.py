#!/usr/bin/env python
# * coding: utf8 *
"""
worker_bee.py

A module that contains logic for building traditional image-based caches.
"""

import os
import shutil
import subprocess
import tempfile
import time
from datetime import date
from os.path import join
from pathlib import Path
from typing import Union, cast

import arcpy
import google.auth
import pygsheets

from . import config, settings, update_data, utilities
from .log import logger, logging_tqdm
from .messaging import send_email
from .resumable import get_job_status, update_job
from .swarm import swarm

AGOL_SCHEME_NAME = "ARCGISONLINE_SCHEME"
SPOT_CACHE_NAME = "spot cache"


def fast_delete_robocopy(target_path: Union[str, Path]) -> None:
    """
    Deletes a directory tree using Windows Robocopy.

    Raises:
        FileNotFoundError: If the target_path does not exist.
        subprocess.CalledProcessError: If Robocopy fails critically (Exit Code >= 8).
        OSError: If the directory cannot be removed after emptying (e.g., active locks).
    """
    target = Path(target_path).resolve()
    logger.info(f"Fast deleting directory: {target}")

    if not target.exists():
        raise FileNotFoundError(f"The directory '{target}' does not exist.")

    # 1. Create a temporary empty directory
    with tempfile.TemporaryDirectory() as empty_source:
        # 2. Construct the Robocopy command
        # /MIR  : Mirror source to target (deletes destination files not in source)
        # /MT:32: Multi-threaded (32 threads)
        # /R:5  : Retry 5 times (increased to handle locked files)
        # /W:1  : Wait 1 second between retries
        # /NP, /NFL, /NDL: Suppress logging for speed
        cmd = [
            "robocopy",
            str(empty_source),
            str(target),
            "/MIR",
            "/MT:32",
            "/R:5",
            "/W:1",
            "/NP",
            "/NFL",
            "/NDL",
        ]

        # 3. Execute
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Robocopy Exit Codes 0-7 indicate success/partial success (e.g., file deletion).
        # Exit Codes >= 8 indicate a critical failure.
        if result.returncode >= 8:
            raise subprocess.CalledProcessError(
                returncode=result.returncode,
                cmd=cmd,
                output=result.stdout,
                stderr=result.stderr,
            )

    # 4. Attempt to remove the root directory.
    # If Robocopy skipped locked files, this will raise OSError: [WinError 145] Directory not empty.
    try:
        shutil.rmtree(target)
    except OSError as e:
        # We catch and re-raise to add context if it's a "Directory not empty" error
        # which is common with ArcGIS locks.
        if getattr(e, "winerror", 0) == 145:  # WinError 145 = Directory not empty
            remaining = len(list(target.iterdir()))
            raise OSError(
                f"Deletion incomplete. {remaining} items remain in '{target.name}'. "
            ) from e
        raise e

    logger.info(f"Successfully deleted directory: {target}")


def parse_levels(levels_txt: str) -> list[float]:
    #: parse the levels parameter text into an array of scales
    min, max = list(map(int, levels_txt.split("-")))

    return settings.SCALES[min : max + 1]


def intersect_scales(scales: list[float], restrict_scales: list[float]) -> list[float]:
    #: return the intersection of between scales and restrict_scales
    intersection = set(scales) & set(restrict_scales)

    return list(intersection)


class WorkerBee(object):
    def __init__(
        self,
        basemap: str,
        missing_only: bool = False,
        skip_update: bool = False,
        skip_test: bool = False,
        spot_path: str | None = None,
        levels: str | None = None,
        dont_wait: bool = False,
    ):
        logger.info("caching {}".format(basemap))
        self.errors = []
        self.start_time = time.time()
        self.basemap = basemap
        self.preview_url = settings.PREVIEW_URL.format(self.basemap.lower())
        self.email_subject = "Cache Update ({})".format(self.basemap)
        basemap_config = config.get_basemap(basemap)
        try:
            self.image_type = basemap_config["imageType"]
        except KeyError:
            self.image_type = None

        utilities.validate_map_layers(basemap)

        if not levels:
            self.restrict_scales = settings.SCALES
        else:
            self.restrict_scales = parse_levels(levels)

        if config.is_dev():
            self.complete_num_bundles = 19
        else:
            self.complete_num_bundles = settings.COMPLETE_NUM_BUNDLES_LU[self.basemap]

        if skip_update or get_job_status("data_updated"):
            logger.info("skipping data update...")
        else:
            update_data.main(dont_wait=dont_wait, basemaps=[basemap])
            send_email(
                self.email_subject, "Data update complete. Proceeding with caching..."
            )

        update_job("data_updated", True)

        if skip_test or get_job_status("test_cache_complete") or spot_path is not None:
            logger.info("skipping test cache...")
        else:
            self.cache_test_extent()

            explode_cache(basemap)

            swarm(
                basemap,
                basemap_config["bucket"],
                self.image_type,
                is_test=True,
                preview_url=self.preview_url,
            )

        update_job("test_cache_complete", True)

        self.missing_only = missing_only
        if self.missing_only:
            logger.info("caching empty tiles only")
        else:
            logger.info("removing previous cache and starting fresh")
            self.delete_cache()

        self.start_bundles = self.get_bundles_count()

        if not spot_path:
            self.overall_progress_bar_current_value = 0
            self.overall_progress_bar = logging_tqdm(
                total=self.complete_num_bundles - self.start_bundles,
                desc="Overall",
                position=0,
            )
            self.cache(not levels)
        else:
            #: levels 0-17 include the entire state
            logger.info("spot caching levels 0-17...")
            self.cache_extent(settings.SCALES[:18], spot_path, SPOT_CACHE_NAME)

            #: levels 18-19 intersect with cache extent
            logger.info(
                "intersecting spot cache polygon with level 18-19 cache extent..."
            )
            intersect = arcpy.analysis.Intersect(
                [spot_path, join(settings.EXTENTSFGDB, settings.EXTENT_18_19)],
                "in_memory/spot_cache_intersect",
                join_attributes="ONLY_FID",
            )
            logger.info("spot caching levels 18-19...")
            self.cache_extent(settings.SCALES[18:], str(intersect), SPOT_CACHE_NAME)

            explode_cache(basemap)

    def cache_extent(
        self,
        scales: list[float],
        aoi: str,
        name: str,
        dont_skip: bool = False,
    ) -> None:
        cache_job_key = f"{name}-{scales}"
        if dont_skip is False and cache_job_key in cast(
            list, get_job_status("cache_extents_completed")
        ):
            logger.info(f"skipping extent based on current job: {cache_job_key}")

            return
        cache_scales = intersect_scales(scales, self.restrict_scales)

        if len(cache_scales) == 0:
            return

        logging_tqdm.write("caching {} at {}".format(name, cache_scales))

        if config.is_dev() and name != SPOT_CACHE_NAME:
            aoi = settings.TEST_EXTENT

        try:
            #: this takes 8-10 minutes to start for some reason
            arcpy.management.ManageTileCache(
                str(settings.CACHES_DIR),
                "RECREATE_EMPTY_TILES",
                in_cache_name=self.basemap,
                in_datasource=utilities.get_pro_map(self.basemap),
                tiling_scheme=AGOL_SCHEME_NAME,
                scales=cache_scales,
                area_of_interest=aoi,
            )

            update_job("cache_extents_completed", cache_job_key)
        except arcpy.ExecuteError:
            self.errors.append([cache_scales, aoi, name])
            logger.error(arcpy.GetMessages())

    def get_progress(self) -> str:
        total_bundles = self.get_bundles_count()

        new_progress_bar_value = total_bundles - self.start_bundles
        self.overall_progress_bar.update(
            new_progress_bar_value - self.overall_progress_bar_current_value
        )
        self.overall_progress_bar_current_value = new_progress_bar_value

        try:
            bundles_per_hour = (total_bundles - self.start_bundles) / (
                (time.time() - self.start_time) / 60 / 60
            )
        except ZeroDivisionError:
            bundles_per_hour = 0
        if bundles_per_hour != 0 and total_bundles > self.start_bundles:
            hours_remaining = (
                self.complete_num_bundles - total_bundles
            ) / bundles_per_hour
        else:
            self.start_time = time.time()
            hours_remaining = "??"
        percent = int(round(float(total_bundles) / self.complete_num_bundles * 100.00))
        msg = "{} of {} ({}%) bundle files created.\nEstimated hours remaining: {}".format(
            total_bundles, self.complete_num_bundles, percent, hours_remaining
        )

        return msg

    def get_bundles_count(self) -> int:
        total_files = 0
        name = self.basemap.replace("/", "_")
        base_folder = Path(settings.CACHES_DIR) / name / name / "_alllayers"
        if base_folder.exists():
            for d in os.listdir(base_folder):
                if d != "missing.jpg":
                    total_files += len(os.listdir(os.path.join(base_folder, d)))

        return total_files

    def cache_test_extent(self) -> None:
        cache_scales = intersect_scales(settings.SCALES, self.restrict_scales)

        self.delete_cache()

        try:
            logger.info("caching test extent")
            #: this takes 8-10 minutes to start for some reason
            arcpy.management.ManageTileCache(
                str(settings.CACHES_DIR),
                "RECREATE_ALL_TILES",
                in_cache_name=self.basemap,
                in_datasource=utilities.get_pro_map(self.basemap),
                tiling_scheme=AGOL_SCHEME_NAME,
                scales=cache_scales,
                area_of_interest=settings.TEST_EXTENT,
            )
        except arcpy.ExecuteError:
            logger.error(arcpy.GetMessages())
            send_email(
                "Cache Test Extent Error ({}) - arcpy.ExecuteError".format(
                    self.basemap
                ),
                arcpy.GetMessages(),
            )
            raise arcpy.ExecuteError

    def delete_cache(self) -> None:
        dir = settings.CACHES_DIR / self.basemap
        if dir.exists():
            logger.info("deleting existing cache")

            fast_delete_robocopy(dir)

        delete_exploded_cache(self.basemap)

    def cache(self, run_all_levels: bool, dont_skip: bool = False) -> None:
        arcpy.env.workspace = settings.EXTENTSFGDB

        for fc_name, scales in settings.CACHE_EXTENTS:
            self.cache_extent(scales, fc_name, fc_name, dont_skip)
            logger.info(self.get_progress())

        send_email(
            self.email_subject,
            "Levels 0-17 completed.\n{}\n{}".format(
                self.get_progress(), self.preview_url
            ),
        )

        for grid in settings.GRIDS:
            total_grids = int(arcpy.management.GetCount(grid[0])[0])
            with arcpy.da.SearchCursor(grid[0], ["SHAPE@", "OID@"]) as cur:
                for row in logging_tqdm(
                    cur, total=total_grids, position=1, desc=f"Level {grid[0]}"
                ):
                    self.cache_extent(
                        [grid[1]],
                        row[0],
                        "{}: OBJECTID: {}".format(grid[0], row[1]),
                        dont_skip,
                    )
                    logger.info(self.get_progress())
            send_email(
                self.email_subject,
                "Level {} completed.\n{}\n{}\nNumber of errors: {}".format(
                    grid[0], self.get_progress(), self.preview_url, len(self.errors)
                ),
            )

        while len(self.errors) > 0:
            msg = "Recaching errors. Errors left: {}".format(len(self.errors))
            logger.warning(msg)
            self.cache_extent(*self.errors.pop())

        bundles = self.get_bundles_count()
        if bundles < self.complete_num_bundles and run_all_levels:
            msg = "Only {} out of {} bundles completed. Recaching...".format(
                bundles, self.complete_num_bundles
            )
            logger.warning(msg)
            self.cache(True, dont_skip=True)

        send_email(self.email_subject + " Finished", "Caching complete!")

        logger.info("updating google spreadsheets")

        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = pygsheets.authorize(custom_credentials=credentials)
        sgid_sheet = client.open_by_key("11ASS7LnxgpnD0jN4utzklREgMf1pcvYjcXcIcESHweQ")
        sgid_worksheet = sgid_sheet[0]
        base_maps_sheet = client.open_by_key(
            "1XnncmhWrIjntlaMfQnMrlcCTyl9e2i-ztbvqryQYXDc"
        )
        base_maps_worksheet = base_maps_sheet[0]

        #: update sgid changelog
        today = date.today().strftime(r"%m/%d/%Y")
        matrix = sgid_worksheet.get_all_values(  # type: ignore
            include_tailing_empty_rows=False, include_tailing_empty=False
        )
        row = [
            today,
            "Complete",
            self.basemap,
            "Recache",
            "Statewide cache rebuild and upload to GCP",
            "stdavis",
            "no",
            "no",
            "no",
            "no",
            "no",
            "no",
            "yes",
        ]
        sgid_worksheet.insert_rows(len(matrix), values=row, inherit=True)  # type: ignore

        #: update base maps spreadsheet embedded in gis.utah.gov page
        this_month = date.today().strftime(r"%b %Y")
        results = base_maps_worksheet.find(self.basemap, matchEntireCell=True)  # type: ignore
        cell = results[0]

        base_maps_worksheet.update_value((cell.row + 1, cell.col), this_month)  # type: ignore

        if not get_job_status("exploding_complete"):
            explode_cache(self.basemap)
            update_job("exploding_complete", True)
            send_email(self.email_subject, "Exploding complete.")
        else:
            logger.info("skipping exploding cache based on job status")


def delete_exploded_cache(basemap) -> None:
    exploded_directory = settings.CACHES_DIR / f"{basemap}_Exploded"
    if exploded_directory.exists():
        fast_delete_robocopy(exploded_directory)


def explode_cache(basemap) -> None:
    delete_exploded_cache(basemap)

    logger.info("exploding cache for {}".format(basemap))
    try:
        arcpy.management.ExportTileCache(
            str(settings.CACHES_DIR / basemap / basemap),
            str(settings.CACHES_DIR),
            f"{basemap}_Exploded",
            export_cache_type="TILE_CACHE",
            storage_format_type="EXPLODED",
        )
    except arcpy.ExecuteError:
        logger.error(arcpy.GetMessages())
        send_email(
            "Explode Cache Error ({}) - arcpy.ExecuteError".format(basemap),
            arcpy.GetMessages(),
        )
        raise arcpy.ExecuteError
    logger.info("exploding complete")
