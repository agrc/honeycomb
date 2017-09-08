#!/usr/bin/env python
# * coding: utf8 *
'''
worker_bee.py

A module that contains logic for building traditional image-based caches.
'''

from . import settings, update_data, config
from .messaging import send_email
import arcpy
import os
import socket
import time


class WorkerBee(object):
    def __init__(self, s_name, missing_only=False, skip_update=False, skip_test=False):
        self.errors = []
        self.start_time = time.time()
        self.service_name = s_name

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

        if missing_only:
            print('caching empty tiles only...')

        self.missing_only = missing_only
        self.start_bundles = self.get_bundles_count()

        self.cache()

    def cache_extent(self, scales, aoi, name):
        print('caching {} at {}'.format(name, scales))

        if config.is_dev():
            aoi = settings.TEST_EXTENT

        try:
            arcpy.server.ManageMapServerCacheTiles(self.service, scales, self.update_mode, settings.NUM_INSTANCES, aoi)
        except arcpy.ExecuteError:
            self.errors.append([scales, aoi, name])
            print(arcpy.GetMessages())
            send_email('Cache Update ({}) - arcpy.ExecuteError'.format(self.service_name), arcpy.GetMessages())

    def get_progress(self):
        total_bundles = self.get_bundles_count()

        bundles_per_hour = (total_bundles - self.start_bundles) / ((time.time() - self.start_time) / 60 / 60)
        if bundles_per_hour != 0 and total_bundles > self.start_bundles:
            hours_remaining = (self.complete_num_bundles - total_bundles) / bundles_per_hour
        else:
            self.start_time = time.time()
            hours_remaining = '??'
        percent = int(round(float(total_bundles) / self.complete_num_bundles * 100.00))
        msg = '{} of {} ({}%) bundle files created.\nEstimated hours remaining: {}'.format(
            total_bundles, self.complete_num_bundles, percent, hours_remaining)
        print(msg)
        return msg

    def get_bundles_count(self):
        totalfiles = 0
        basefolder = os.path.join(settings.CACHE_DIR, self.service_name.replace('/', '_'), 'Layers', '_alllayers')
        for d in os.listdir(basefolder):
            if d != 'missing.jpg':
                totalfiles += len(os.listdir(os.path.join(basefolder, d)))
        return totalfiles

    def cache_test_extent(self):
        print('caching test extent')
        try:
            arcpy.server.ManageMapServerCacheTiles(self.service, settings.SCALES, 'RECREATE_ALL_TILES', settings.NUM_INSTANCES, settings.TEST_EXTENT)
            send_email('Cache Test Extent Complete ({})'.format(self.service_name), self.preview_url)
            if raw_input('Recache test extent (T) or continue with full cache (F): ') == 'T':
                self.cache_test_extent()
        except arcpy.ExecuteError:
            print(arcpy.GetMessages())
            send_email('Cache Test Extent Error ({}) - arcpy.ExecuteError'.format(self.service_name), arcpy.GetMessages())
            raise arcpy.ExecuteError

    def cache(self):
        arcpy.env.workspace = settings.EXTENTSFGDB
        if self.missing_only:
            self.update_mode = 'RECREATE_EMPTY_TILES'
            print('Caching empty tiles only')
        else:
            self.update_mode = 'RECREATE_ALL_TILES'
            print('Caching all tiles')

        for extent in settings.CACHE_EXTENTS:
            self.cache_extent(extent[1], extent[0], extent[0])

        send_email(self.email_subject,
                   'Levels 0-9 completed.\n{}\n{}'.format(self.get_progress(), self.preview_url))

        if config.is_dev():
            settings.GRIDS = settings.GRIDS[:-4]
        for grid in settings.GRIDS:
            total_grids = int(arcpy.management.GetCount(grid[0])[0])
            grid_count = 0
            progress = ''
            with arcpy.da.SearchCursor(grid[0], ['SHAPE@', 'OID@']) as cur:
                for row in cur:
                    grid_count += 1
                    grid_percent = int(round((float(grid_count) / total_grids) * 100))
                    self.cache_extent(grid[1], row[0], '{}: OBJECTID: {}'.format(grid[0], row[1]))
                    grit_percent_msg = 'Grids for this level completed: {}%'.format(grid_percent)
                    print(grit_percent_msg)
                    progress = self.get_progress()
            send_email(self.email_subject, 'Level {} completed.\n{}\n{}\nNumber of errors: {}'.format(grid[0], progress, self.preview_url, len(self.errors)))

        while (len(self.errors) > 0):
            msg = 'Recaching errors. Errors left: {}'.format(len(self.errors))
            print(msg)
            send_email(self.email_subject, msg)
            self.cache_extent(*self.errors.pop())

        bundles = self.get_bundles_count()
        if bundles < self.complete_num_bundles:
            msg = 'Only {} out of {} bundles completed. Recaching...'.format(bundles, self.complete_num_bundles)
            print(msg)
            send_email(self.email_subject, msg)
            self.cache()

        send_email(self.email_subject + ' Finished', 'Caching complete!\n\n{}'.format(self.preview_url))
