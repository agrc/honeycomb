"""
TODO:
- update google spreadsheet with last updated date
- loop through all regularly updated caches
- republish mxd possibly using arcgis press (may need to delete and recreate if there are problems getting the service to update)
"""
import arcpy
import os
import time
import shutil
import sys
from agrc import messaging
from agrc import logging
from agrc import update
from agrc import arcpy_helpers
import update_data
import settings

extentsFGDB = r'C:\Cache\MapData\Extents.gdb'
cache_dir = r'C:\arcgisserver\directories\arcgiscache'
pallet = r'C:\Cache\cache_pallet.py'
test_extent = os.path.join(extentsFGDB, 'test_extent')
complete_num_bundles_lu = {
    'BaseMaps/Terrain': 2087,
    'BaseMaps/Vector': 2087,
    'BaseMaps/Topo': 2087,
    'BaseMaps/Lite': 2060,
    'BaseMaps/Overlay': 2060,
    'BaseMaps/Hybrid': 13611,
    'BaseMaps/AddressPoints': 1842,
    'Lite': 21885,
    'Terrain': 22136,
    'Overlay': 21878,
    'AddressPoints': 18924,
    'NAIP2016_Color1Meter_4Band': 9670,
    'NAIP2016_Color1Meter_4Band_NRG': 9670
}

num_instances = 6
pauseAtNight = False
extra_wgs_scales = [
    591657527.591555,
    295828763.795777,
    147914381.897889,
    73957190.948944,
    36978595.474472
]
all_scales = [
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

    # hybrid only
    # 564.248588,
    # 282.124294
]

extent_0_2 = 'CacheExtent_0_2'
extent_3_4 = 'CacheExtent_3_4'
extent_5_10 = 'CacheExtent_5_9'
cache_extents = [
    [extent_0_2, all_scales[0:3]],
    [extent_3_4, all_scales[3:5]],
    [extent_5_10, all_scales[5:10]]
]

grids10 = 'CacheGrids_10'
grids11 = 'CacheGrids_11'
grids12 = 'CacheGrids_12'
grids13 = 'CacheGrids_13'
grids14 = 'CacheGrids_14'
grids15 = 'CacheGrids_15'
grids16 = 'CacheGrids_16'
grids = [
    [grids10, all_scales[10]],
    [grids11, all_scales[11]],
    [grids12, all_scales[12]],
    [grids13, all_scales[13]],
    [grids14, all_scales[14]]

    # hybrid only
    # [grids15, all_scales[15]],
    # [grids16, all_scales[16]]
]

errors = []
emailer = messaging.Emailer('stdavis@utah.gov', testing=False)
logger = logging.Logger()
start_time = time.time()

def cache_extent(scales, aoi, name):
    logger.logMsg('caching {} at {}'.format(name, scales))

    try:
        arcpy.ManageMapServerCacheTiles_server(service, scales, update_mode, num_instances, aoi)
    except arcpy.ExecuteError:
        errors.append([scales, aoi, name])
        logger.logMsg('arcpy.ExecuteError')
        logger.logError()
        logger.logGPMsg()
        emailer.sendEmail('Cache Update ({}) - arcpy.ExecuteError'.format(service_name), logger.log)

def get_progress():
    global start_time
    total_bundles = get_bundles_count()

    bundles_per_hour = (total_bundles - start_bundles)/((time.time() - start_time)/60/60)
    if bundles_per_hour != 0 and total_bundles > start_bundles:
        hours_remaining = (complete_num_bundles - total_bundles) / bundles_per_hour
    else:
        start_time = time.time()
        hours_remaining = '??'
    percent = int(round(float(total_bundles)/complete_num_bundles * 100.00))
    msg = '{} of {} ({}%) bundle files created.\nEstimated hours remaining: {}'.format(
        total_bundles, complete_num_bundles, percent, hours_remaining)
    logger.logMsg(msg)
    return msg

def get_bundles_count():
    totalfiles = 0
    basefolder = os.path.join(cache_dir, service_name.replace('/', '_'), 'Layers', '_alllayers')
    for d in os.listdir(basefolder):
        if d != 'missing.jpg':
            totalfiles += len(os.listdir(os.path.join(basefolder, d)))
    return totalfiles

def cache_test_extent():
    logger.logMsg('caching test extent')
    try:
        arcpy.ManageMapServerCacheTiles_server(service, all_scales, 'RECREATE_ALL_TILES', num_instances, test_extent)
        emailer.sendEmail('Cache Test Extent Complete ({})'.format(service_name), preview_url)
        if raw_input('Recache test extent (T) or continue with full cache (F): ') == 'T':
            cache_test_extent()
    except arcpy.ExecuteError:
        logger.logMsg('arcpy.ExecuteError')
        logger.logError()
        logger.logGPMsg()
        emailer.sendEmail('Cache Test Extent Error ({}) - arcpy.ExecuteError'.format(service_name), logger.log)
        raise arcpy.ExecuteError


def cache():
    arcpy.env.workspace = extentsFGDB
    global update_mode
    if update_mode == 'Y':
        update_mode = 'RECREATE_ALL_TILES'
    else:
        update_mode = 'RECREATE_EMPTY_TILES'

    if 'BaseMaps' not in service_name:
        cache_extent(extra_wgs_scales, extent_0_2, 'extra web mercator scales')

    for extent in cache_extents:
        cache_extent(extent[1], extent[0], extent[0])

    emailer.sendEmail(email_subject,
                      'Levels 0-9 completed.\n{}\n{}'.format(get_progress(), preview_url))

    for grid in grids:
        total_grids = int(arcpy.GetCount_management(grid[0]).getOutput(0))
        grid_count = 0
        step = 10
        currentStep = step
        with arcpy.da.SearchCursor(grid[0], ['SHAPE@', 'OID@']) as cur:
            for row in cur:
                grid_count += 1
                grid_percent = int(round((float(grid_count)/total_grids)*100))
                cache_extent(grid[1], row[0], '{}: OBJECTID: {}'.format(grid[0], row[1]))
                grit_percent_msg = 'Grids for this level completed: {}%'.format(grid_percent)
                logger.logMsg(grit_percent_msg)
                progress = get_progress()
        emailer.sendEmail(email_subject, 'Level {} completed.\n{}\n{}\nNumber of errors: {}'.format(grid[0], progress, preview_url, len(errors)))

    while (len(errors) > 0):
        msg = 'Recaching errors. Errors left: {}'.format(len(errors))
        logger.logMsg(msg)
        emailer.sendEmail(email_subject, msg)
        cache_extent(*errors.pop())

    bundles = get_bundles_count()
    if bundles < complete_num_bundles:
        msg = 'Only {} out of {} bundles completed. Recaching...'.format(bundles, complete_num_bundles)
        logger.logMsg(msg)
        emailer.sendEmail(email_subject, msg)
        cache()

    emailer.sendEmail(email_subject + ' Finished', 'Caching complete!\n\n{}\n\n{}'.format(preview_url, logger.log))

    logger.writeLogToFile()


def main(s_name, overwrite, update, test):
    global service_name
    service_name = s_name
    global complete_num_bundles
    complete_num_bundles = complete_num_bundles_lu[service_name]
    global preview_url
    preview_url = settings.PREVIEW_URL.format(service_name)
    """
    import socket
    socket.gethostbyname(socket.gethostname())
    """
    global service
    service = r'C:\Users\agrc-arcgis\AppData\Roaming\ESRI\Desktop10.4\ArcCatalog\arcgis on localhost_6080 (admin)\{}.MapServer'.format(service_name)
    global email_subject
    email_subject = 'Cache Update ({})'.format(service_name)
    if update == 'Y':
        update_data.main()
        emailer.sendEmail(email_subject, 'Data update complete. Proceeding with caching...')
    if test == 'Y':
        cache_test_extent()
    global update_mode
    update_mode = overwrite
    global start_bundles
    start_bundles = get_bundles_count()

    cache()

if __name__ == '__main__':
    arg_prompts = ['Cache name with folder ( e.g. "Terrain"): ',
                   'Overwrite existing tiles? (Y/N) ',
                   'Update data? (Y/N): ',
                   'Run a test cache? (Y/N): ']
    args = []
    for i, prompt in enumerate(arg_prompts):
        try:
            args.append(sys.argv[i + 1])
        except IndexError:
            args.append(raw_input(prompt))

    main(*args)
