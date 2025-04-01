#!/usr/bin/env python
# * coding: utf8 *
"""
__ini__.py

A module that contains settings for honeycomb.
"""

import os
from pathlib import Path

import arcpy

SHARE_ENV_NAME = "HONEYCOMB_SHARE"
SHARE = os.getenv(SHARE_ENV_NAME)
PRO_PROJECT = Path(SHARE) / "Maps" / "Maps.aprx"
QUAD_WORD = os.getenv("HONEYCOMB_QUAD_WORD")
if SHARE is None:
    raise Exception(
        'Please set the "{}" environmental variable!'.format(SHARE_ENV_NAME)
    )
PREVIEW_URL = rf"https://discover.agrc.utah.gov/login/path/{QUAD_WORD}/tiles/preview#basemap_{{}}_test/8/39.527/-111.555"
DATA_FOLDER = Path(__file__).parent / "data"
EXTENTSFGDB = str(DATA_FOLDER / "Extents.geodatabase")
CACHES_DIR = Path(r"C:\Cache\Caches")
CACHES_DIR.mkdir(exist_ok=True)
TEST_EXTENT = os.path.join(EXTENTSFGDB, "test_extent")

COMPLETE_NUM_BUNDLES_LU = {
    "Lite": 20509,
    "Terrain": 20511,
    "Overlay": 2934,
    "AddressPoints": 18924,
}

SCALES = [
    591657527.591555,  #: 0
    295828763.795777,  #: 1
    147914381.897889,  #: 2
    73957190.948944,  #: 3
    36978595.474472,  #: 4
    18489297.737236,  #: 5
    9244648.868618,  #: 6
    4622324.434309,  #: 7
    2311162.217155,  #: 8
    1155581.108577,  #: 9
    577790.554289,  #: 10
    288895.277144,  #: 11
    144447.638572,  #: 12
    72223.819286,  #: 13
    36111.909643,  #: 14
    18055.954822,  #: 15
    9027.977411,  #: 16
    4513.988705,  #: 17
    2256.994353,  #: 18
    1128.497176,  #: 19
]

EXTENT_0_7 = "CacheExtent_0_7"
EXTENT_8_9 = "CacheExtent_8_9"
EXTENT_10_17 = "CacheExtent_10_17"
CACHE_EXTENTS = [
    [EXTENT_0_7, SCALES[0:8]],
    [EXTENT_8_9, SCALES[8:10]],
    [EXTENT_10_17, SCALES[10:18]],
]

EXTENT_18_19 = "CacheExtent_18_19"

GRIDS18_19 = "CacheGrids_4_18_19"
GRIDS = [
    [GRIDS18_19, SCALES[18]],
    [GRIDS18_19, SCALES[19]],
]

arcpy.env.parallelProcessingFactor = "95%"
#: required for using the RECREATE_EMPTY_TILES option in the Manage Tile Cache tool
arcpy.env.overwriteOutput = True
