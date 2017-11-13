#!/usr/bin/env python
# * coding: utf8 *
'''
publish.py

A module that contains code for publishing mxd's to ArcGIS Server for raster caches.
'''

from os import mkdir, remove
from os.path import abspath, dirname, exists, join

import arcpy

from . import config


def publish(basemap):
    mxd_path = join(config.get_config_value('mxdFolder'), basemap + '.mxd')
    drafts_folder = join(config.config_folder, 'sddrafts')
    sddraft_path = join(drafts_folder, basemap + '.sddraft')

    if not exists(drafts_folder):
        mkdir(drafts_folder)

    print('creating .sddraft')
    arcpy.mapping.CreateMapSDDraft(mxd_path, sddraft_path, basemap,
                                   connection_file_path=config.ags_connection_file)

    print('analyzing')
    analysis = arcpy.mapping.AnalyzeForSD(sddraft_path)
    print('The following information was returned during analysis of the MXD:')
    for key in ('messages', 'warnings', 'errors'):
        items = analysis[key]
        if len(items) > 0:
            print(key.upper())
            for ((message, code), layerlist) in items.iteritems():
                print('{} (CODE {})'.format(message, code))

                if len(layerlist) > 0:
                    print('applies to:')
                    for layer in layerlist:
                        print(layer.name + '\n')

    if analysis['errors'] == {}:
        print('staging')
        sd_path = sddraft_path.replace('.sddraft', '.sd')
        if exists(sd_path):
            remove(sd_path)
        arcpy.server.StageService(sddraft_path, sd_path)

        print('uploading')
        arcpy.server.UploadServiceDefinition(sd_path, config.ags_connection_file)

        print('defining cache scheme')
        service = join(config.ags_connection_file.replace('.ags', ''), basemap + '.MapServer')
        print(service)
        arcpy.server.CreateMapServerCache(service,
                                          r'C:\arcgisserver\directories\arcgiscache',
                                          'PREDEFINED',
                                          'STANDARD',
                                          20,
                                          96,
                                          "256 x 256",
                                          predefined_tiling_scheme=join(abspath(dirname(__file__)), 'data', 'Conf.xml'))
        print('service published successfully!')
    else:
        print('Service could not be published because of errors found during analysis. Please fix them and republish.')
