#!/usr/bin/env python
# * coding: utf8 *
"""
update_data.py

A module that contains code for updating the data for base maps.
"""

import datetime
import logging
import os
import sys
import time
from pathlib import Path

import arcpy
import pyodbc
import pytz
from forklift import engine

from . import config, settings
from .log import logger, logging_tqdm

LOCAL = Path(r"C:\Cache\MapData")
SHARE = Path(settings.SHARE) / "Data"  # type: ignore
SGID = SHARE / "SGID.sde"
SGID_GDB_NAME = "SGID10_WGS.gdb"
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

    conn = pyodbc.connect(os.getenv("HONEYCOMB_INTERNAL_CONNECTION_STRING"))
    cursor = conn.cursor()

    #: get a list of all tables
    cursor.execute(
        """
        SELECT database_name, owner, table_name
        FROM sde.SDE_Table_Registry
        WHERE owner <> 'SDE'
        """
    )
    tables = cursor.fetchall()

    table_dict = {
        table[2].upper(): f"{table[0]}.{table[1]}.{table[2]}" for table in tables
    }

    return table_dict


def get_layers(basemaps: list[str] | None = None):
    """
    Get a list of SGID layers that are sources in any of the cache map documents
    """
    layers = set()

    maps = {}
    if basemaps:
        for basemap in basemaps:
            basemap_config = config.get_basemap(basemap)
            maps.setdefault(basemap_config.get("mapName", basemap), {}).setdefault(
                "groupLayers", set()
            ).update(basemap_config.get("groupLayers", []))

    logger.info("getting unique data sources from layers")
    project = arcpy.mp.ArcGISProject(str(settings.PRO_PROJECT))
    group_layers = []
    for map in project.listMaps():
        if basemaps:
            if map.name not in maps:
                continue
            else:
                group_layers = maps[map.name].get("groupLayers", [])
        logger.info(f"map: {map.name}")
        for layer in map.listLayers():
            if layer.isFeatureLayer and SGID_GDB_NAME in layer.dataSource:
                if len(group_layers) > 0:
                    if layer.longName.split("\\")[0] not in group_layers:
                        continue
                layers.add(Path(layer.dataSource).name)

    return list(layers)


def sgid(basemaps: list[str] | None = None):
    sgid_fcs = get_SGID_lookup()

    local_db = str(LOCAL / SGID_GDB_NAME)

    if not arcpy.Exists(local_db):
        logger.info(f"creating: {local_db}")
        arcpy.CreateFileGDB_management(str(LOCAL), SGID_GDB_NAME)

    sgid_layers = get_layers(basemaps)
    logger.info(f"updating {str(len(sgid_layers))} layers in {local_db}...")

    with arcpy.EnvManager(workspace=local_db):
        #: set the postfix to the first layer name so we can see it in the progress bar on the first iteration
        progress_bar = logging_tqdm(sgid_layers, postfix=sgid_layers[0])
        index = 0
        for fc in progress_bar:
            try:
                sgid_name = sgid_fcs[fc.upper()]
            except KeyError:
                logger.warning(
                    f"Table not found in internal: {fc}. No update will be performed."
                )
                continue
            finally:
                #: this won't show up until the next loop iteration so we need to update it with the
                #: next layer name
                index += 1
                if index < len(sgid_layers) - 1:
                    progress_bar.set_postfix_str(sgid_layers[index])
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


def update_statewide_parcels():
    local_gdb = LOCAL / "StatewideParcels.gdb"
    if not local_gdb.exists():
        logger.info(f"creating: {local_gdb}")
        arcpy.CreateFileGDB_management(str(local_gdb.parent), local_gdb.name)

    local = str(local_gdb / "StateWideParcels")

    logger.info(f"updating statewide parcels in {local}...")
    if arcpy.Exists(local):
        logger.info(f"deleting: {local}")
        arcpy.management.Delete(local)

    arcpy.conversion.ExportFeatures(
        "https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahStatewideParcels/FeatureServer/0",
        local,
    )


def main(
    static_only: bool = False,
    sgid_only: bool = False,
    external_only: bool = False,
    dont_wait: bool = False,
    basemaps: list[str] | None = None,
):
    if basemaps is not None and "StatewideParcels" in basemaps:
        #: statewide parcels is a special case. It only has a single layer and the
        #: source is in AGOL.
        update_statewide_parcels()

        return

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
        sgid(basemaps)

    if static_only or all:
        static()

    # Zach doesn't use these datasets yet anyways and we should probably take forklift out of the equation
    # if external_only or all:
    #     pallet_path = Path(__file__).parent / "pallets" / "BasemapsPallet.py"
    #     run_forklift(str(pallet_path))
