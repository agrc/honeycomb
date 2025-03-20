#!/usr/bin/env python
# * coding: utf8 *
"""
update_data.py

A module that contains code for updating the data for base maps.
"""

import datetime
import logging
import sys
import time
from pathlib import Path

import arcpy
import pytz
from forklift import engine

from . import settings
from .log import logger, logging_tqdm

LOCAL = Path(r"C:\Cache\MapData")
SHARE = Path(settings.SHARE) / "Data"
SGID = SHARE / "SGID.sde"
SGID_GDB_NAME = "SGID10_WGS.gdb"
PRO_PROJECT = Path(settings.SHARE) / "Maps" / "Maps.aprx"
STATIC_GDB_NAME = "UtahBaseMap-Data_WGS.gdb"


def run_forklift(pallet_path=None):
    logger.info("running forklift")

    log = logging.getLogger("forklift")
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    log.addHandler(console_handler)
    log.setLevel(logging.DEBUG)

    engine.build_pallets(pallet_path)
    engine.lift_pallets(pallet_path)
    engine.ship_data()


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
        for layer in logging_tqdm(map.listLayers()):
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
        progress_bar = logging_tqdm(sgid_layers)
        for fc in progress_bar:
            progress_bar.set_postfix_str(fc)
            try:
                sgid_name = sgid_fcs[fc]
            except KeyError:
                logger.warning(
                    f"Table not found in internal: {fc}. No update will be performed."
                )
                continue
            if arcpy.Exists(fc):
                arcpy.management.Delete(fc)
            arcpy.management.Project(
                str(SGID / sgid_name),
                fc,
                arcpy.SpatialReference(3857),
                "NAD_1983_To_WGS_1984_5",
            )


def static():
    local_static = str(LOCAL / STATIC_GDB_NAME)
    if arcpy.Exists(local_static):
        logger.info(f"deleting: {local_static}")
        arcpy.management.Delete(local_static)

    logger.info(f"copying: {STATIC_GDB_NAME}")
    arcpy.management.Copy(str(SHARE / STATIC_GDB_NAME), local_static)


def main(static_only=False, sgid_only=False, external_only=False, dont_wait=False):
    if not LOCAL.exists():
        logger.info(f"creating local folder: {LOCAL}")
        LOCAL.mkdir(parents=True)

    all = not static_only and not sgid_only and not external_only

    #: wait until 10 PM to run
    mountain = pytz.timezone("US/Mountain")
    now = datetime.datetime.now(mountain)
    start = now.replace(hour=22, minute=0, second=0, microsecond=0)

    if not dont_wait and now < start:
        diff = start - now
        logger.info(f"waiting {diff} until 10 PM to update data")
        time.sleep(diff.seconds)

    if sgid_only or all:
        sgid()

    if static_only or all:
        static()

    if external_only or all:
        pallet_path = Path(__file__).parent / "pallets" / "BasemapsPallet.py"
        run_forklift(str(pallet_path))
