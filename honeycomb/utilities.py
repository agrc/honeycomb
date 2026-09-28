from pathlib import Path
from shutil import copy

import arcpy

from . import config, settings
from .log import logger


def get_cache_directory(basemap: str) -> Path:
    cache_location = config.get_basemap(basemap).get("cacheLocation")
    return Path(cache_location) if cache_location else settings.CACHES_DIR


def get_pro_map(basemap: str, cache_directory: Path | None = None) -> arcpy._mp.Map:
    #: make a copy of the pro project so that we don't keep a lock on it
    #: append the name of the cache so that we can run multiple caches at once without lock issues
    cache_directory = cache_directory or get_cache_directory(basemap)
    temp_project_path = cache_directory / "TempProjects" / f"Maps_{basemap}.aprx"
    temp_project_path.unlink(missing_ok=True)
    temp_project_path.parent.mkdir(parents=True, exist_ok=True)
    copy(settings.PRO_PROJECT, temp_project_path)

    project = arcpy.mp.ArcGISProject(str(temp_project_path))
    maps = project.listMaps(basemap)
    if not maps:
        raise Exception(f"Map '{basemap}' not found in project.")
    pro_map = maps[0]
    pro_map.clearSelection()
    pro_map.defaultCamera.setExtent(
        #: western states
        arcpy.Extent(
            XMin=-13885235,
            XMax=-11359207,
            YMin=3675964,
            YMax=6275285,
            spatial_reference=arcpy.SpatialReference(3857),
        )
    )

    if not pro_map:
        raise Exception(f"Map '{basemap}' not found in project.")

    return pro_map


def validate_map_layers(basemap: str, cache_directory: Path | None = None) -> None:
    pro_map = get_pro_map(basemap, cache_directory)
    broken_layers = [
        f"{layer.longName} ({layer.dataSource})"
        for layer in pro_map.listLayers()
        if layer.isBroken
    ]
    if len(broken_layers) > 0:
        raise Exception(
            f"The following layers are broken in the '{pro_map.name}' map:\n"
            + "\n".join(broken_layers)
        )
    logger.info(f'All layers in the "{pro_map.name}" map are valid.')

    #: release schema lock so that we can update data in a future step
    del pro_map
