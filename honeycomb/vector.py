"""
vector.py

A module for publishing vector tiles to ArcGIS Online.
"""

import logging
import os
import sys
from datetime import date
from os.path import join

import arcgis
import arcpy
import google.auth
import pygsheets
from forklift import engine

from . import config

BASE_FOLDER = config.get_config_value("vectorTilesFolder")
USERNAME = os.getenv("HONEYCOMB_AGOL_USERNAME")
PASSWORD = os.getenv("HONEYCOMB_AGOL_PASSWORD")


def update_data():
    print("running forklift")

    log = logging.getLogger("forklift")
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    log.addHandler(console_handler)
    log.setLevel(logging.DEBUG)

    engine.build_pallets(None)
    engine.lift_pallets(None)
    engine.ship_data()


def main(base_map_name, config):
    print("building tiles for: " + base_map_name)

    project_path = join(BASE_FOLDER, base_map_name)
    promap = arcpy.mp.ArcGISProject(join(project_path, base_map_name + ".aprx")).listMaps()[0]
    tile_package = join(project_path, base_map_name + "_temp" + ".vtpk")

    print("building package...")
    if arcpy.Exists(tile_package):
        arcpy.management.Delete(tile_package)

    arcpy.management.CreateVectorTilePackage(
        promap,
        tile_package,
        "ONLINE",
        tile_structure="INDEXED",
        min_cached_scale=295828763.795778,
        max_cached_scale=564.248588,
        summary=config["summary"],
        tags=config["tags"],
    )

    print("publishing new tile package item...")
    gis = arcgis.gis.GIS(username=USERNAME, password=PASSWORD)
    item = gis.content.add({}, data=tile_package)

    print("publishing new vector tiles service...")
    temp_item = item.publish()

    print("replacing production service...")
    prod_item = arcgis.gis.Item(gis, config["id"])
    gis.content.replace_service(prod_item, temp_item)

    print("removing temporary items...")
    gis.content.delete_items([item, temp_item])

    print("vector tile package successfully built and published!")

    print("updating base maps spreadsheet")
    credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = pygsheets.authorize(custom_credentials=credentials)
    base_maps_sheet = client.open_by_key("1XnncmhWrIjntlaMfQnMrlcCTyl9e2i-ztbvqryQYXDc")
    base_maps_worksheet = base_maps_sheet[0]

    today = date.today().strftime(r"%m/%d/%Y")
    results = base_maps_worksheet.find(base_map_name, includeFormulas=True)
    cell = results[0]

    base_maps_worksheet.update_value((cell.row + 1, cell.col), today)
