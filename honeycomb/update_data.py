#!/usr/bin/env python
# * coding: utf8 *
'''
update_data.py

A module that contains code for updating the data for base maps.
'''

from os.path import join

import arcpy

from . import settings

LOCAL = r'C:\Cache\MapData'
SHARE = join(settings.SHARE, 'Maps', 'Data')
SGID = join(SHARE, 'SGID10.sde')
SGID_GDB_NAME = 'SGID10_WGS.gdb'


def get_SGID_lookup():
    '''
    Get a dictionary of all of the feature classes in SGID for matching
    them with the local FGDB feature classes.
    '''
    print('getting SGID fc lookup')
    sgid_fcs = {}
    arcpy.env.workspace = SGID
    for fc in arcpy.ListFeatureClasses():
        sgid_fcs[fc.split('.')[-1]] = fc

    return sgid_fcs


def main():
    sgid_fcs = get_SGID_lookup()

    print('updating SGID data on SHARE')
    arcpy.env.workspace = join(SHARE, SGID_GDB_NAME)
    for fc in arcpy.ListFeatureClasses():
        print(fc)
        arcpy.management.Delete(fc)
        arcpy.management.Project(join(SGID, sgid_fcs[fc]), fc, arcpy.SpatialReference(3857), 'NAD_1983_To_WGS_1984_5')

    print('copying databases locally')
    for db in [SGID_GDB_NAME, 'UtahBaseMap-Data_WGS.gdb']:
        local_db = join(LOCAL, db)
        SHARE_db = join(SHARE, db)
        arcpy.management.Delete(local_db)
        arcpy.management.Copy(SHARE_db, local_db)

    arcpy.env.workspace = None
