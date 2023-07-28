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

import arcpy
import google.auth
import pygsheets

from . import config, settings, update_data
from .log import logger, logging_tqdm
from .messaging import send_email
from .resumable import get_job_status, update_job
from .swarm import swarm

spot_cache_name = "spot cache"
error_001470_message = "ERROR 001470: Failed to retrieve the job status from server. The Job is running on the server, please use the above URL to check the job status.\nFailed to execute (ManageMapServerCacheTiles).\n"  # noqa


def parse_levels(levels_txt):
    #: parse the levels parameter text into an array of scales
    min, max = list(map(int, levels_txt.split("-")))

    return settings.SCALES[min : max + 1]


def intersect_scales(scales, restrict_scales):
    #: return the intersection of between scales and restrict_scales
    intersection = set(scales) & set(restrict_scales)

    return list(intersection)


class WorkerBee(object):
    def __init__(
        self,
        basemap,
        missing_only=False,
        skip_update=False,
        skip_test=False,
        spot_path=False,
        levels=False,
        dont_wait=False,
    ):
        logger.info("caching {}".format(basemap))
        self.errors = []
        self.start_time = time.time()
        self.service_name = basemap

        if not levels:
            self.restrict_scales = settings.SCALES
        else:
            self.restrict_scales = parse_levels(levels)

        if config.is_dev():
            self.complete_num_bundles = 19
        else:
            self.complete_num_bundles = settings.COMPLETE_NUM_BUNDLES_LU[self.service_name]

        self.preview_url = settings.PREVIEW_URL.format(self.service_name.lower())

        self.service = os.path.join(config.get_ags_connection(), "{}.MapServer".format(self.service_name))
        self.email_subject = "Cache Update ({})".format(self.service_name)

        if skip_update or get_job_status("data_updated"):
            logger.info("skipping data update...")
        else:
            update_data.main(dont_wait=dont_wait)
            send_email(self.email_subject, "Data update complete. Proceeding with caching...")

        update_job("data_updated", True)

        if skip_test or get_job_status("test_cache_complete"):
            logger.info("skipping test cache...")
        else:
            self.cache_test_extent()
            basemap_info = config.get_basemap(basemap)
            swarm(basemap, basemap_info["bucket"], is_test=True, preview_url=self.preview_url)
            if input("Test cache complete. Would you like to continue processing the production cache? (y/n) ") != "y":
                raise Exception("caching cancelled")

        update_job("test_cache_complete", True)

        self.missing_only = missing_only
        self.start_bundles = self.get_bundles_count()

        if self.missing_only:
            self.update_mode = "RECREATE_EMPTY_TILES"
            logger.info("Caching empty tiles only")
        else:
            self.update_mode = "RECREATE_ALL_TILES"
            logger.info("Caching all tiles")

        if not spot_path:
            self.overall_progress_bar_current_value = 0
            self.overall_progress_bar = logging_tqdm(
                total=self.complete_num_bundles - self.start_bundles, desc="Overall", position=0
            )
            self.cache(not levels)
        else:
            #: levels 0-17 include the entire state
            logger.info("spot caching levels 0-17...")
            self.cache_extent(settings.SCALES[:18], spot_path, spot_cache_name)

            #: levels 18-19 intersect with cache extent
            logger.info("intersecting spot cache polygon with level 18-19 cache extent...")
            intersect = arcpy.analysis.Intersect(
                [spot_path, join(settings.EXTENTSFGDB, settings.EXTENT_18_19)],
                "in_memory/spot_cache_intersect",
                join_attributes="ONLY_FID",
            )
            logger.info("spot caching levels 18-19...")
            self.cache_extent(settings.SCALES[18:], intersect, spot_cache_name)

    def cache_extent(self, scales, aoi, name):
        cache_job_key = f"{name}-{scales}"
        if cache_job_key in get_job_status("cache_extents_completed"):
            logger.info(f"skipping extent based on current job: {cache_job_key}")

            return
        cache_scales = intersect_scales(scales, self.restrict_scales)

        if len(cache_scales) == 0:
            return

        logging_tqdm.write("caching {} at {}".format(name, cache_scales))

        if config.is_dev() and name != spot_cache_name:
            aoi = settings.TEST_EXTENT

        try:
            arcpy.server.ManageMapServerCacheTiles(
                self.service, cache_scales, self.update_mode, settings.NUM_INSTANCES, aoi
            )
            #: the gp tool in cache_test_extent messes with the conda/python environment causing the following error message:
            #: "ModuleNotFoundError: No module named 'multiprocess'"
            #: resetting the environment seems to solve the issue.
            arcpy.ResetEnvironments()

            update_job("cache_extents_completed", cache_job_key)
        except arcpy.ExecuteError as e:
            if hasattr(e, "message") and e.message == error_001470_message:
                msg = "ERROR 001470 thrown. Moving on and hoping the job completes successfully."
                logger.warning(msg)
                send_email(
                    "Cache Warning (ERROR 001470)", "e.message\n\narcpy.GetMessages:\n{}".format(arcpy.GetMessages())
                )
            else:
                self.errors.append([cache_scales, aoi, name])
                logger.error(arcpy.GetMessages())
                send_email("Cache Update ({}) - arcpy.ExecuteError".format(self.service_name), arcpy.GetMessages())

    def get_progress(self):
        total_bundles = self.get_bundles_count()

        new_progress_bar_value = total_bundles - self.start_bundles
        self.overall_progress_bar.update(new_progress_bar_value - self.overall_progress_bar_current_value)
        self.overall_progress_bar_current_value = new_progress_bar_value

        bundles_per_hour = (total_bundles - self.start_bundles) / ((time.time() - self.start_time) / 60 / 60)
        if bundles_per_hour != 0 and total_bundles > self.start_bundles:
            hours_remaining = (self.complete_num_bundles - total_bundles) / bundles_per_hour
        else:
            self.start_time = time.time()
            hours_remaining = "??"
        percent = int(round(float(total_bundles) / self.complete_num_bundles * 100.00))
        msg = "{} of {} ({}%) bundle files created.\nEstimated hours remaining: {}".format(
            total_bundles, self.complete_num_bundles, percent, hours_remaining
        )
        return msg

    def get_bundles_count(self):
        totalfiles = 0
        name = self.service_name.replace("/", "_")
        basefolder = Path(settings.CACHE_DIR) / name / name / "_alllayers"
        for d in os.listdir(basefolder):
            if d != "missing.jpg":
                totalfiles += len(os.listdir(os.path.join(basefolder, d)))
        return totalfiles

    def cache_test_extent(self):
        logger.info("caching test extent")
        cache_scales = intersect_scales(settings.SCALES, self.restrict_scales)

        try:
            arcpy.server.ManageMapServerCacheTiles(
                self.service, cache_scales, "RECREATE_ALL_TILES", settings.NUM_INSTANCES, settings.TEST_EXTENT
            )
            #: the gp tool in cache_test_extent messes with the conda/python environment causing the following error message:
            #: "ModuleNotFoundError: No module named 'multiprocess'"
            #: resetting the environment seems to solve the issue.
            arcpy.ResetEnvironments()
        except arcpy.ExecuteError:
            logger.error(arcpy.GetMessages())
            send_email(
                "Cache Test Extent Error ({}) - arcpy.ExecuteError".format(self.service_name), arcpy.GetMessages()
            )
            raise arcpy.ExecuteError

    def cache(self, run_all_levels):
        arcpy.env.workspace = settings.EXTENTSFGDB

        for fc_name, scales in settings.CACHE_EXTENTS:
            self.cache_extent(scales, fc_name, fc_name)
            self.get_progress()

        send_email(self.email_subject, "Levels 0-9 completed.\n{}\n{}".format(self.get_progress(), self.preview_url))

        if config.is_dev():
            settings.GRIDS = settings.GRIDS[:-4]
        for grid in settings.GRIDS:
            total_grids = int(arcpy.management.GetCount(grid[0])[0])
            with arcpy.da.SearchCursor(grid[0], ["SHAPE@", "OID@"]) as cur:
                for row in logging_tqdm(cur, total=total_grids, position=1, desc="Current"):
                    self.cache_extent([grid[1]], row[0], "{}: OBJECTID: {}".format(grid[0], row[1]))
                    self.get_progress()
            send_email(
                self.email_subject,
                "Level {} completed.\n{}\n{}\nNumber of errors: {}".format(
                    grid[0], self.get_progress(), self.preview_url, len(self.errors)
                ),
            )

        while len(self.errors) > 0:
            msg = "Recaching errors. Errors left: {}".format(len(self.errors))
            logger.warning(msg)
            send_email(self.email_subject, msg)
            self.cache_extent(*self.errors.pop())

        bundles = self.get_bundles_count()
        if bundles < self.complete_num_bundles and run_all_levels:
            msg = "Only {} out of {} bundles completed. Recaching...".format(bundles, self.complete_num_bundles)
            logger.warning(msg)
            send_email(self.email_subject, msg)
            self.cache(True)

        send_email(self.email_subject + " Finished", "Caching complete!")

        logger.info("updating google spreadsheets")

        credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = pygsheets.authorize(custom_credentials=credentials)
        sgid_sheet = client.open_by_key("11ASS7LnxgpnD0jN4utzklREgMf1pcvYjcXcIcESHweQ")
        sgid_worksheet = sgid_sheet[0]
        base_maps_sheet = client.open_by_key("1XnncmhWrIjntlaMfQnMrlcCTyl9e2i-ztbvqryQYXDc")
        base_maps_worksheet = base_maps_sheet[0]

        #: update sgid changelog
        today = date.today().strftime(r"%m/%d/%Y")
        matrix = sgid_worksheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False)
        row = [
            today,
            "Complete",
            self.service_name,
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
        results = base_maps_worksheet.find(self.service_name, matchEntireCell=True)
        cell = results[0]

        base_maps_worksheet.update_value((cell.row + 1, cell.col), this_month)
