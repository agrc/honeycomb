#!/usr/bin/env python
# * coding: utf8 *
'''
__ini__.py

A module that contains settings for honeycomb.
'''
import os

SHARE_ENV_NAME = 'HONEYCOMB_SHARE'
SHARE = os.getenv(SHARE_ENV_NAME)
if SHARE is None:
    raise Exception('Please set the "{}" environmental variable!'.format(SHARE_ENV_NAME))
PREVIEW_URL = r'http://{}/arcgis/rest/services/{}/MapServer?f=jsapi'
EXTENTSFGDB = os.path.join(os.path.dirname(__file__), 'data', 'Extents.gdb')
CACHE_DIR = r'E:\arcgisserver\directories\arcgiscache'
TEST_EXTENT = os.path.join(EXTENTSFGDB, 'test_extent')

COMPLETE_NUM_BUNDLES_LU = {
    'Lite': 20509,
    'Terrain': 20511,
    'Overlay': 20511,
    'AddressPoints': 18924,
    'NAIP2016_Color1Meter_4Band': 9670,
    'NAIP2016_Color1Meter_4Band_NRG': 9670
}

NUM_INSTANCES = 6
SCALES = [
    591657527.591555,   #: 0
    295828763.795777,   #: 1
    147914381.897889,   #: 2
    73957190.948944,    #: 3
    36978595.474472,    #: 4
    1.8489297737236E7,  #: 5
    9244648.868618,     #: 6
    4622324.434309,     #: 7

    2311162.217155,     #: 8
    1155581.108577,     #: 9

    577790.554289,      #: 10
    288895.277144,      #: 11
    144447.638572,      #: 12
    72223.819286,       #: 13
    36111.909643,       #: 14

    18055.954822,       #: 15
    9027.977411,        #: 16
    4513.988705,        #: 17
    2256.994353,        #: 18
    1128.497176         #: 19
]

EXTENT_0_7 = 'CacheExtent_0_7'
EXTENT_8_9 = 'CacheExtent_8_9'
EXTENT_10_14 = 'CacheExtent_10_17'
CACHE_EXTENTS = [
    [EXTENT_0_7, SCALES[0:8]],
    [EXTENT_8_9, SCALES[8:10]],
    [EXTENT_10_14, SCALES[10:15]]
]

EXTENT_18_19 = 'CacheExtent_18_19'

GRIDS15 = 'CacheGrids_15'
GRIDS16 = 'CacheGrids_16'
GRIDS17 = 'CacheGrids_17'
GRIDS18 = 'CacheGrids_18'
GRIDS19 = 'CacheGrids_19'
GRIDS = [
    [GRIDS15, SCALES[15]],
    [GRIDS16, SCALES[16]],
    [GRIDS17, SCALES[17]],
    [GRIDS18, SCALES[18]],
    [GRIDS19, SCALES[19]]
]
