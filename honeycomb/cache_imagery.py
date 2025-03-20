from pathlib import Path
from shutil import rmtree

import arcpy
from settings import SCALES

from .log import logger

current_directory = Path(__file__).parent.absolute()
pro_project_path = r"D:\NAIP2021.aprx"
cache_directory = Path(r"D:\Cache")

if (
    cache_directory.exists()
    and input(f"do you want to delete the {cache_directory} folder? (y/n): ") == "y"
):
    logger.info(f"clearing out: {str(cache_directory)}")
    rmtree(cache_directory)

    cache_directory.mkdir()

map = "CIR"
local_project = arcpy.mp.ArcGISProject(pro_project_path)
pro_map = local_project.listMaps(map)[0]

arcpy.env.parallelProcessingFactor = "85%"

min_cached_scale = SCALES[0]
max_cached_scale = SCALES[18]
logger.info(f"building cache for scales from {min_cached_scale} to {max_cached_scale}")
test_extent = (
    Path(r"C:\dev\honeycomb\honeycomb\data")
    / "Extents.geodatabase"
    / "main.test_extent"
)
project_extent = Path(r"D:\NAIP2021.gdb\NAIP2021_RGB_Boundary")
arcpy.management.ManageTileCache(
    str(cache_directory),
    manage_mode="RECREATE_EMPTY_TILES",
    in_cache_name=f"{map}_compact",
    in_datasource=pro_map,
    tiling_scheme="ARCGISONLINE_SCHEME",
    area_of_interest=str(project_extent),
    min_cached_scale=min_cached_scale,
    max_cached_scale=max_cached_scale,
)

# # bug still exists if run in a script... it doesn't explode the cache
# arcpy.management.ExportTileCache(str(cache_directory / f'{map}_compact' / map), str(cache_directory), map,
#     export_cache_type='TILE_CACHE', storage_format_type='EXPLODED')

logger.info("\n\nThe next step is to run the export tile cache tool from the Pro UI")
