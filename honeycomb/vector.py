"""
vector.py

A module for publishing vector tiles to ArcGIS Online.
"""

import os
from datetime import date
from shutil import rmtree

import arcgis
import arcpy
import google.auth
import pygsheets

from . import settings, stats, update_data, utilities
from .log import logger
from .messaging import send_email

USERNAME = os.getenv("HONEYCOMB_AGOL_USERNAME")
PASSWORD = os.getenv("HONEYCOMB_AGOL_PASSWORD")


def main(
    basemap: str,
    config: dict,
    skip_update: bool = False,
    dont_wait: bool = False,
):
    logger.info("building tiles for: " + basemap)

    if config["mapName"]:
        mapName = config["mapName"]
    else:
        mapName = basemap

    utilities.validate_map_layers(mapName)

    if not skip_update:
        update_data.main(basemaps=[basemap], dont_wait=dont_wait)

    promap = utilities.get_pro_map(mapName)

    if config["groupLayers"]:
        for layer in promap.listLayers():
            #: we only want to set the visibility of root-level group layers
            if layer.isGroupLayer and layer.longName == layer.name:
                visible = layer.name in config["groupLayers"]
                logger.info(
                    f"setting visibility for group layer: {layer.name} to: {visible}"
                )
                layer.visible = visible

    tile_packages_path = settings.CACHES_DIR / "TilePackages"
    index_gdb_path = tile_packages_path / "TileIndexes.gdb"

    if not index_gdb_path.exists():
        logger.info("creating tile index geodatabase...")
        arcpy.management.CreateFileGDB(
            out_folder_path=str(index_gdb_path.parent), out_name=index_gdb_path.name
        )

    index_path = index_gdb_path / f"{basemap}_TileIndex"
    if not arcpy.Exists(index_path):
        logger.info("creating tile index...")
        arcpy.management.CreateVectorTileIndex(
            promap,
            str(index_path),
            "ONLINE",
        )

    logger.info("building package...")
    tile_package_path = tile_packages_path / f"{basemap}_temp.vtpk"
    tile_package_path.unlink(missing_ok=True)
    temp_tiles_folder = tile_package_path.with_suffix("")
    if temp_tiles_folder.exists():
        rmtree(temp_tiles_folder)
    tile_package_path.parent.mkdir(parents=True, exist_ok=True)

    stats.record_start(basemap, "cache")

    arcpy.management.CreateVectorTilePackage(
        promap,
        str(tile_package_path),
        "ONLINE",
        tile_structure="INDEXED",
        min_cached_scale=295828763.795778,
        max_cached_scale=564.248588,
        index_polygons=str(index_path),
        summary=config["summary"],
        tags=config["tags"],
    )

    #: record finish here since there is an async pause below while waiting for approval to replace the production service
    stats.record_finish(basemap, "cache")

    logger.info("publishing new tile package item...")
    gis = arcgis.gis.GIS(username=USERNAME, password=PASSWORD)
    temp_folder = gis.content.folders.get(folder="Temp")
    item_properties = arcgis.gis.ItemProperties(
        title=tile_package_path.stem,
        item_type=arcgis.gis.ItemTypeEnum.VECTOR_TILE_PACKAGE.value,
    )
    job = temp_folder.add(item_properties, file=str(tile_package_path))

    item = job.result(60 * 10)  #: 10 minute timeout

    logger.info("publishing new vector tiles service...")
    temp_item = item.publish()
    temp_item.sharing.sharing_level = arcgis.gis.SharingLevel.ORG

    send_email(
        f"Tile Package Generation Complete for {basemap}",
        f"Check out the temporary service here: https://www.arcgis.com/apps/mapviewer/index.html?basemapUrl={temp_item.url}. Once you are happy with the service, go back to the honeycomb server and press enter to continue with the replacement.",
    )
    input(
        f"""
        *************
        Tile Package Generation Complete for {basemap}. Check out the temporary service here: https://www.arcgis.com/apps/mapviewer/index.html?basemapUrl={temp_item.urls}. Press enter to continue with the replacement.
        *************
        """
    )

    stats.record_start(basemap, "upload")
    logger.info("replacing production service...")
    prod_item = arcgis.gis.Item(gis, config["id"])
    gis.content.replace_service(prod_item, temp_item)

    logger.info("removing temporary items...")
    gis.content.delete_items([item, temp_item])

    logger.info("vector tile package successfully built and published!")
    stats.record_finish(basemap, "upload")

    logger.info("updating base maps spreadsheet")
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = pygsheets.authorize(custom_credentials=credentials)
    base_maps_sheet = client.open_by_key("1XnncmhWrIjntlaMfQnMrlcCTyl9e2i-ztbvqryQYXDc")
    base_maps_worksheet = base_maps_sheet[0]

    today = date.today().strftime(r"%m/%d/%Y")
    results = base_maps_worksheet.find(basemap, includeFormulas=True)
    cell = results[0]

    base_maps_worksheet.update_value((cell.row + 1, cell.col), today)
