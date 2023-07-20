#!/usr/bin/env python
# * coding: utf8 *
"""
update_data.py

A module that contains code for updating the data for base maps.
"""

from pathlib import Path

import arcpy
from tqdm import tqdm

from . import settings
from .log import logger

LOCAL = Path(r"C:\Cache\MapData")
SHARE = Path(settings.SHARE) / "Data"
SGID = SHARE / "SGID.sde"
SGID_GDB_NAME = "SGID10_WGS.gdb"
PRO_PROJECT = Path(settings.SHARE) / "Maps" / "Maps.aprx"
STATIC_GDB_NAME = "UtahBaseMap-Data_WGS.gdb"


def get_SGID_lookup():
    """
    Get a dictionary of all of the feature classes in SGID for matching
    them with the local FGDB feature classes.
    """
    logger.info("getting SGID fc lookup")
    sgid_fcs = {}
    arcpy.env.workspace = str(SGID)
    for fc in arcpy.ListFeatureClasses():
        sgid_fcs[fc.split(".")[-1]] = fc

    return sgid_fcs


def get_layers():
    """
    Get a list of SGID layers that are sources in any of the cache map documents
    """
    layers = set()

    logger.info("getting unique data sources from layers")
    project = arcpy.mp.ArcGISProject(str(PRO_PROJECT))
    for map in project.listMaps():
        logger.info(f"map: {map.name}")
        for layer in tqdm(map.listLayers()):
            if layer.isFeatureLayer and SGID_GDB_NAME in layer.dataSource:
                layers.add(Path(layer.dataSource).name)

    return list(layers)


def sgid():
    sgid_fcs = get_SGID_lookup()

    local_db = str(LOCAL / SGID_GDB_NAME)

    if not arcpy.Exists(local_db):
        logger.info(f"creating: {local_db}")
        arcpy.CreateFileGDB_management(str(LOCAL), SGID_GDB_NAME)

    sgid_layers = get_layers()
    logger.info(f"updating: {local_db}...")
    with arcpy.EnvManager(workspace=local_db):
        progress_bar = tqdm(sgid_layers)
        for fc in progress_bar:
            progress_bar.set_postfix_str(fc)
            if arcpy.Exists(fc):
                arcpy.management.Delete(fc)
            arcpy.management.Project(
                str(SGID / sgid_fcs[fc]), fc, arcpy.SpatialReference(3857), "NAD_1983_To_WGS_1984_5"
            )


def static():
    local_static = str(LOCAL / STATIC_GDB_NAME)
    if arcpy.Exists(local_static):
        logger.info(f"deleting: {local_static}")
        arcpy.management.Delete(local_static)

    logger.info(f"copying: {STATIC_GDB_NAME}")
    arcpy.management.Copy(str(SHARE / STATIC_GDB_NAME), local_static)


def main(static_only=False, sgid_only=False):
    if not LOCAL.exists():
        logger.info(f"creating local folder: {LOCAL}")
        LOCAL.mkdir(parents=True)

    neither = not static_only and not sgid_only

    if sgid_only or neither:
        sgid()

    if static_only or neither:
        static()
