#!/usr/bin/env python
# * coding: utf8 *
'''
update_data.py

A module that contains code for updating the data for base maps.
'''

from os.path import join
import psycopg2

import arcpy

from . import settings
from config import config_folder
import logger

LOCAL = r'C:\MapData'
SGID = join(config_folder, 'SGID10.sde')
SGID_GDB_NAME = 'SGID10_WGS.gdb'


def get_SGID_lookup():
    '''
    Get a dictionary of all of the feature classes in SGID for matching
    them with the local FGDB feature classes.
    '''
    logger.info('getting SGID fc lookup')
    sgid_fcs = {}
    connection = psycopg2.connect(dbname='sgid', user='agrc', password='agrc', host='35.235.99.102')
    cursor = connection.cursor()
    cursor.execute('SELECT table_schema, table_name FROM information_schema.tables')
    for schema, name in cursor.fetchall():
        sgid_fcs[name.upper()] = 'sgid.{}.{}'.format(schema, name)

    cursor.close()
    connection.close()

    return sgid_fcs


def main():
    sgid_fcs = get_SGID_lookup()

    logger.info('updating SGID data')
    arcpy.env.workspace = join(LOCAL, SGID_GDB_NAME)
    for fc in arcpy.ListFeatureClasses():
        logger.info(fc)
        arcpy.management.Delete(fc)
        arcpy.management.Project(join(SGID, sgid_fcs[fc.upper()]), fc, arcpy.SpatialReference(3857), 'NAD_1983_To_WGS_1984_5')

    arcpy.env.workspace = None
