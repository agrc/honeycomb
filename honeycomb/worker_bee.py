#!/usr/bin/env python
# * coding: utf8 *
"""
worker_bee.py

A module that contains logic for building traditional image-based caches.
"""

import os
import time
from datetime import date
from os.path import join
from pathlib import Path
from shutil import rmtree

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


def parse_levels(levels_txt):
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
        spot_path: bool = False,
        levels: bool = False,
        dont_wait: bool = False,
    ):
        logger.info("caching {}".format(basemap))
        self.errors = []
        self.start_time = time.time()
        self.basemap = basemap
        self.preview_url = settings.PREVIEW_URL.format(self.basemap.lower())
        self.email_subject = "Cache Update ({})".format(self.basemap)
        basemap_config = config.get_basemap(basemap)
        self.image_type = basemap_config["imageType"]

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

        if skip_test or get_job_status("test_cache_complete"):
            logger.info("skipping test cache...")
        else:
            self.cache_test_extent()

            self.explode_cache()

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
            self.cache_extent(settings.SCALES[18:], intersect, SPOT_CACHE_NAME)

            self.explode_cache()

    def cache_extent(
        self,
        scales: list[float],
        aoi: str,
        name: str,
        dont_skip: bool = False,
    ) -> None:
        cache_job_key = f"{name}-{scales}"
        if dont_skip is False and cache_job_key in get_job_status(
            "cache_extents_completed"
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
            print(arcpy.env.parallelProcessingFactor)
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

    def explode_cache(self) -> None:
        logger.info("exploding cache")

        # todo after Pro v3.5, remove the next two lines, and uncomment the ExportTileCache line
        send_email(
            f"Cache Job Complete {self.basemap}",
            "Time to manually convert cache to exploded format.",
        )
        input(
            "Caching complete. Manually convert cache to exploded format and then press enter to continue..."
        )

        # try:
        #     arcpy.management.ExportTileCache(
        #         str(settings.CACHES_DIR / self.basemap / self.basemap),
        #         str(settings.CACHES_DIR),
        #         f"{self.basemap}_Exploded",
        #         export_cache_type="TILE_CACHE",
        #         storage_format_type="EXPLODED",
        #     )
        # except arcpy.ExecuteError:
        #     logger.error(arcpy.GetMessages())
        #     send_email(
        #         "Explode Cache Error ({}) - arcpy.ExecuteError".format(self.basemap),
        #         arcpy.GetMessages(),
        #     )
        #     raise arcpy.ExecuteError

    def delete_cache(self) -> None:
        dir = settings.CACHES_DIR / self.basemap
        if dir.exists():
            logger.info("deleting existing cache")

            rmtree(dir)

        exploded_directory = settings.CACHES_DIR / f"{self.basemap}_Exploded"
        if exploded_directory.exists():
            logger.info("deleting existing exploded cache")
            rmtree(exploded_directory)

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
        matrix = sgid_worksheet.get_all_values(
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
        sgid_worksheet.insert_rows(len(matrix), values=row, inherit=True)

        #: update base maps spreadsheet embedded in gis.utah.gov page
        this_month = date.today().strftime(r"%b %Y")
        results = base_maps_worksheet.find(self.basemap, matchEntireCell=True)
        cell = results[0]

        base_maps_worksheet.update_value((cell.row + 1, cell.col), this_month)

        if not get_job_status("exploding_complete"):
            self.explode_cache()
            update_job("exploding_complete", True)
            send_email(self.email_subject, "Exploding complete.")
        else:
            logger.info("skipping exploding cache based on job status")
