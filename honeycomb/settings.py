#!/usr/bin/env python
# * coding: utf8 *
'''
__ini__.py

A module that contains settings for honeycomb.
'''
import os


HNAS_ENV_NAME = 'HONEYCOMB_HNAS'
if os.getenv(HNAS_ENV_NAME) is not None:
    HNAS = os.getenv('HONEYCOMB_HNAS')
else:
    print('Please set the "HONEYCOMP_HNAS" environmental variable!')
PREVIEW_URL = r'http://{}/arcgis/rest/services/{}/MapServer?f=jsapi'
EXTENTSFGDB = r'C:\Cache\MapData\Extents.gdb'
CACHE_DIR = r'C:\arcgisserver\directories\arcgiscache'
TEST_EXTENT = os.path.join(EXTENTSFGDB, 'test_extent')
COMPLETE_NUM_BUNDLES_LU = {
    'Lite': 21885,
    'Terrain': 22136,
    'Overlay': 21878,
    'AddressPoints': 18924,
    'NAIP2016_Color1Meter_4Band': 9670,
    'NAIP2016_Color1Meter_4Band_NRG': 9670
}

NUM_INSTANCES = 6
SCALES = [
    591657527.591555,
    295828763.795777,
    147914381.897889,
    73957190.948944,
    36978595.474472,

    1.8489297737236E7,
    9244648.868618,
    4622324.434309,
    2311162.217155,
    1155581.108577,
    577790.554289,
    288895.277144,
    144447.638572,
    72223.819286,
    36111.909643,
    18055.954822,
    9027.977411,
    4513.988705,
    2256.994353,
    1128.497176
]

EXTENT_0_2 = 'CacheExtent_0_2'
EXTENT_3_4 = 'CacheExtent_3_4'
EXTENT_5_10 = 'CacheExtent_5_9'
CACHE_EXTENTS = [
    [EXTENT_0_2, SCALES[0:8]],
    [EXTENT_3_4, SCALES[8:10]],
    [EXTENT_5_10, SCALES[10:15]]
]

GRIDS10 = 'CacheGrids_10'
GRIDS11 = 'CacheGrids_11'
GRIDS12 = 'CacheGrids_12'
GRIDS13 = 'CacheGrids_13'
GRIDS14 = 'CacheGrids_14'
GRIDS15 = 'CacheGrids_15'
GRIDS16 = 'CacheGrids_16'
GRIDS = [
    [GRIDS10, SCALES[10]],
    [GRIDS11, SCALES[11]],
    [GRIDS12, SCALES[12]],
    [GRIDS13, SCALES[13]],
    [GRIDS14, SCALES[14]]
]
