#!/usr/bin/env python
# * coding: utf8 *
'''
worker_bee.py

A module that contains logic for building traditional image-based caches.
'''

import os
import socket
import time
from os.path import join, dirname, realpath
from shutil import rmtree
import pygsheets
from datetime import date
from pathlib import Path
from tqdm import tqdm

import arcpy

from . import config, settings, update_data
from .messaging import send_email

spot_cache_name = 'spot cache'
error_001470_message = 'ERROR 001470: Failed to retrieve the job status from server. The Job is running on the server, please use the above URL to check the job status.\nFailed to execute (ManageMapServerCacheTiles).\n'  # noqa


def parse_levels(levels_txt):
    #: parse the levels parameter text into an array of scales
    min, max = list(map(int, levels_txt.split('-')))

    return settings.SCALES[min:max + 1]


def intersect_scales(scales, restrict_scales):
    #: return the intersection of between scales and restrict_scales
    intersection = set(scales) & set(restrict_scales)

    return list(intersection)


class WorkerBee(object):
    def __init__(self, s_name, missing_only=False, skip_update=False, skip_test=False, spot_path=False, levels=False):
        print('caching {}'.format(s_name))
        self.errors = []
        self.start_time = time.time()
        self.service_name = s_name

        if not levels:
            self.restrict_scales = settings.SCALES
        else:
            self.restrict_scales = parse_levels(levels)

        try:
            print('deleting previous *_GCS folder, if any')
            rmtree(os.path.join(settings.CACHE_DIR, s_name + '_GCS'))
        except Exception:
            pass

        if config.is_dev():
            self.complete_num_bundles = 19
        else:
            self.complete_num_bundles = settings.COMPLETE_NUM_BUNDLES_LU[self.service_name]

        ip = socket.gethostbyname(socket.gethostname())
        self.preview_url = settings.PREVIEW_URL.format(ip, self.service_name)

        self.service = os.path.join(config.get_ags_connection(), '{}.MapServer'.format(self.service_name))
        self.email_subject = 'Cache Update ({})'.format(self.service_name)

        if skip_update:
            print('skipping data update...')
        else:
            update_data.main()
            send_email(self.email_subject, 'Data update complete. Proceeding with caching...')

        if skip_test:
            print('skipping test cache...')
        else:
            self.cache_test_extent()

        self.missing_only = missing_only
        self.start_bundles = self.get_bundles_count()

        if self.missing_only:
            self.update_mode = 'RECREATE_EMPTY_TILES'
            print('Caching empty tiles only')
        else:
            self.update_mode = 'RECREATE_ALL_TILES'
            print('Caching all tiles')

        if not spot_path:
            self.overall_progress_bar = tqdm(total=self.complete_num_bundles - self.start_bundles, desc='Overall', position=0)
            self.cache(not levels)
        else:
            #: levels 0-17 include the entire state
            print('spot caching levels 0-17...')
            self.cache_extent(settings.SCALES[:18], spot_path, spot_cache_name)

            #: levels 18-19 intersect with cache extent
            print('intersecting spot cache polygon with level 18-19 cache extent...')
            intersect = arcpy.analysis.Intersect([spot_path, join(settings.EXTENTSFGDB, settings.EXTENT_18_19)],
                                                 'in_memory/spot_cache_intersect',
                                                 join_attributes='ONLY_FID')
            print('spot caching levels 18-19...')
            self.cache_extent(settings.SCALES[18:], intersect, spot_cache_name)

    def cache_extent(self, scales, aoi, name):
        cache_scales = intersect_scales(scales, self.restrict_scales)

        if len(cache_scales) == 0:
            return

        tqdm.write('caching {} at {}'.format(name, cache_scales))

        if config.is_dev() and name != spot_cache_name:
            aoi = settings.TEST_EXTENT

        try:
            arcpy.server.ManageMapServerCacheTiles(self.service, cache_scales, self.update_mode, settings.NUM_INSTANCES, aoi)
        except arcpy.ExecuteError as e:
            if e.message == error_001470_message:
                msg = 'ERROR 001470 thrown. Moving on and hoping the job completes successfully.'
                print(msg)
                send_email('Cache Warning (ERROR 001470)', 'e.message\n\narcpy.GetMessages:\n{}'.format(arcpy.GetMessages().encode('utf-8')))
            else:
                self.errors.append([cache_scales, aoi, name])
                print(arcpy.GetMessages().encode('utf-8'))
                send_email('Cache Update ({}) - arcpy.ExecuteError'.format(self.service_name), arcpy.GetMessages().encode('utf-8'))

    def get_progress(self):
        total_bundles = self.get_bundles_count()

        self.overall_progress_bar.update(total_bundles - self.start_bundles)

        bundles_per_hour = (total_bundles - self.start_bundles) / ((time.time() - self.start_time) / 60 / 60)
        if bundles_per_hour != 0 and total_bundles > self.start_bundles:
            hours_remaining = (self.complete_num_bundles - total_bundles) / bundles_per_hour
        else:
            self.start_time = time.time()
            hours_remaining = '??'
        percent = int(round(float(total_bundles) / self.complete_num_bundles * 100.00))
        msg = '{} of {} ({}%) bundle files created.\nEstimated hours remaining: {}'.format(
            total_bundles, self.complete_num_bundles, percent, hours_remaining)
        return msg

    def get_bundles_count(self):
        totalfiles = 0
        name = self.service_name.replace('/', '_')
        basefolder = Path(settings.CACHE_DIR) / name / name / '_alllayers'
        for d in os.listdir(basefolder):
            if d != 'missing.jpg':
                totalfiles += len(os.listdir(os.path.join(basefolder, d)))
        return totalfiles

    def cache_test_extent(self):
        print('caching test extent')
        cache_scales = intersect_scales(settings.SCALES, self.restrict_scales)

        try:
            arcpy.server.ManageMapServerCacheTiles(self.service, cache_scales, 'RECREATE_ALL_TILES', settings.NUM_INSTANCES, settings.TEST_EXTENT)
            send_email('Cache Test Extent Complete ({})'.format(self.service_name), self.preview_url)
            # if raw_input('Recache test extent (T) or continue with full cache (F): ') == 'T':
            #     self.cache_test_extent()
        except arcpy.ExecuteError:
            print(arcpy.GetMessages().encode('utf-8'))
            send_email('Cache Test Extent Error ({}) - arcpy.ExecuteError'.format(self.service_name), arcpy.GetMessages().encode('utf-8'))
            raise arcpy.ExecuteError

    def cache(self, run_all_levels):
        arcpy.env.workspace = settings.EXTENTSFGDB

        for fc_name, scales in settings.CACHE_EXTENTS:
            self.cache_extent(scales, fc_name, fc_name)
            self.get_progress()

        send_email(self.email_subject,
                   'Levels 0-9 completed.\n{}\n{}'.format(self.get_progress(), self.preview_url))

        if config.is_dev():
            settings.GRIDS = settings.GRIDS[:-4]
        for grid in settings.GRIDS:
            total_grids = int(arcpy.management.GetCount(grid[0])[0])
            with arcpy.da.SearchCursor(grid[0], ['SHAPE@', 'OID@']) as cur:
                for row in tqdm(cur, total=total_grids, position=1, desc='Current Job'):
                    self.cache_extent([grid[1]], row[0], '{}: OBJECTID: {}'.format(grid[0], row[1]))
                    self.get_progress()
            send_email(self.email_subject, 'Level {} completed.\n{}\n{}\nNumber of errors: {}'.format(grid[0], self.get_progress(), self.preview_url, len(self.errors)))

        while (len(self.errors) > 0):
            msg = 'Recaching errors. Errors left: {}'.format(len(self.errors))
            print(msg)
            send_email(self.email_subject, msg)
            self.cache_extent(*self.errors.pop())

        bundles = self.get_bundles_count()
        if bundles < self.complete_num_bundles and run_all_levels:
            msg = 'Only {} out of {} bundles completed. Recaching...'.format(bundles, self.complete_num_bundles)
            print(msg)
            send_email(self.email_subject, msg)
            self.cache(True)

        send_email(self.email_subject + ' Finished', 'Caching complete!\n\n{}'.format(self.preview_url))

        print('updating google spreadsheets')

        client = pygsheets.authorize(service_file=join(dirname(realpath(__file__)), 'service-account.json'))
        sgid_sheet = client.open_by_key('11ASS7LnxgpnD0jN4utzklREgMf1pcvYjcXcIcESHweQ')
        sgid_worksheet = sgid_sheet[0]
        base_maps_sheet = client.open_by_key('1XnncmhWrIjntlaMfQnMrlcCTyl9e2i-ztbvqryQYXDc')
        base_maps_worksheet = base_maps_sheet[0]

        #: update sgid changelog
        today = date.today().strftime(r'%m/%d/%Y')
        matrix = sgid_worksheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False)
        row = [today, 'Complete', self.service_name, 'Recache', 'Statewide cache rebuild and upload to GCP', 'stdavis', 'no', 'no', 'no', 'no', 'no', 'no', 'yes']
        sgid_worksheet.insert_rows(len(matrix), values=row, inherit=True)

        #: update base maps spreadsheet embedded in gis.utah.gov page
        this_month = date.today().strftime(r'%b %Y')
        results = base_maps_worksheet.find(self.service_name, matchEntireCell=True)
        cell = results[0]

        base_maps_worksheet.update_value((cell.row + 1, cell.col), this_month)
