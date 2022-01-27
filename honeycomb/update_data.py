#!/usr/bin/env python
# * coding: utf8 *
'''
update_data.py

A module that contains code for updating the data for base maps.
'''

from pathlib import Path

import arcpy

from . import settings

LOCAL = Path(r'C:\Cache\MapData')
SHARE = Path(settings.SHARE) / 'Data'
SGID = SHARE / 'SGID.sde'
SGID_GDB_NAME = 'SGID10_WGS.gdb'


def get_SGID_lookup():
    '''
    Get a dictionary of all of the feature classes in SGID for matching
    them with the local FGDB feature classes.
    '''
    print('getting SGID fc lookup')
    sgid_fcs = {}
    arcpy.env.workspace = str(SGID)
    for fc in arcpy.ListFeatureClasses():
        sgid_fcs[fc.split('.')[-1]] = fc

    return sgid_fcs


def main():
    sgid_fcs = get_SGID_lookup()

    if not LOCAL.exists:
        print('creating local folder')
        LOCAL.mkdir(parents=True)

    print('updating SGID data on SHARE')
    arcpy.env.workspace = str(SHARE / SGID_GDB_NAME)
    for fc in arcpy.ListFeatureClasses():
        print(fc)
        arcpy.management.Delete(fc)
        arcpy.management.Project(str(SGID / sgid_fcs[fc]), fc, arcpy.SpatialReference(3857), 'NAD_1983_To_WGS_1984_5')

    print('copying databases locally')
    for db in [SGID_GDB_NAME, 'UtahBaseMap-Data_WGS.gdb']:
        local_db = str(LOCAL / db)
        if not arcpy.Exists(local_db):
            print(f'creating: {local_db}')
            arcpy.CreateFileGDB_management(LOCAL, db)

        SHARE_db = str(SHARE / db)
        arcpy.management.Delete(local_db)
        arcpy.management.Copy(SHARE_db, local_db)

    arcpy.env.workspace = None
