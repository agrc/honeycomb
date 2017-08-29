AGS_CACHE_DIR = r'C:\arcgisserver\directories\arcgiscache'
# AGS_CACHE_DIR = r'C:\Cache\tile-etl\test-data'

from agrc import messaging
from sys import argv
import os
import shutil
import subprocess
import glob
import threading
import traceback
from time import sleep


CACHES = {
    # FolderName: Bucket
    'UploadTestService': ('state-of-utah-test', 'jpeg'),
    'BaseMaps_Imagery_HRO2012Color6Inch_4Band': ('state-of-utah-hro-2012-rgb', 'png'),
    'JPG_Service': ('state-of-utah-test', 'jpeg'),
    'Lite': ('state-of-utah-lite-tiles/Lite', 'jpeg'),
    'Overlay': ('state-of-utah-pyramid-tiles-overlay/Overlay', 'png'),
    'Terrain': ('state-of-utah-pyramid-tiles-terrain/Terrain', 'jpeg'),
    'NAIP2016_Color1Meter_4Band': ('state-of-utah-naip-2016-rgb', 'jpeg'),
    'NAIP2016_Color1Meter_4Band_NRG': ('state-of-utah-naip-2016-nrg', 'jpeg'),
    'Topo': ('state-of-utah-topo-tiles/Topo', 'jpeg'),
    'AddressPoints': ('state-of-utah-pyramid-tiles-address-points/AddressPoints', 'png'),
    'Hillshade': ('state-of-utah-pyramid-tiles-hillshade/Hillshade', 'jpeg')
}

try:
    cache_folder_name = argv[1]
except:
    cache_folder_name = raw_input('Cache Folder Name (e.g. BaseMaps_Terrain): ')

new_folder = os.path.join(AGS_CACHE_DIR, cache_folder_name + '_GCS')
emailer = messaging.Emailer('stdavis@utah.gov', testing=False)
base_folder = os.path.join(AGS_CACHE_DIR, cache_folder_name, r'Layers\_alllayers')
bucket, image_type = CACHES[cache_folder_name]
content_type = 'image/{}'.format(image_type)
script_folder = os.path.dirname(os.path.abspath(__file__))

try:
    print('deleting old *_GCS folder')
    shutil.rmtree(new_folder)
except:
    pass

def process_level(level):
    try:
        print('etl-ing level: {}'.format(level))
        new_level = str(int(level[1:]))
        new_level_folder = os.path.join(new_folder, new_level)
        os.makedirs(new_level_folder)
        print('globbing')
        paths = glob.glob('{}/{}/**/*.*[!.lock]'.format(base_folder, level))
        print('processing folders')
        for file_path in paths:
            parts = file_path.split(os.path.sep)[-2:]
            row = str(int(parts[0][1:], 16))
            column = str(int(parts[1][1:-4], 16))
            ext = parts[1][-3:]
            column_folder = os.path.join(new_level_folder, column)
            if not os.path.exists(column_folder):
                os.mkdir(column_folder)
            shutil.copy2(os.path.join(base_folder, level, file_path), os.path.join(column_folder, row))

        print('uploading level: {}'.format(new_level))
        subprocess.check_call([
            r'C:\Python27\ArcGIS10.4\python.exe',
            r'C:\gsutil\gsutil',
            '-m',
            '-h',
            'Content-Type:' + content_type,
            'cp',
            '-a',
            'public-read',
            '-r',
            new_level_folder,
            'gs://' + bucket
        ])
        print('uploading complete: {}'.format(new_level))
    except Exception as e:
        trace = traceback.format_exc()
        emailer.sendEmail('Uploading error. Level: {}'.format(level), trace)
        print(trace)
        raise e

    try:
        print('removing local folders')
        sleep(1) #: give time for gsutil to release locks on files
        shutil.rmtree(os.path.join(base_folder, level))
        shutil.rmtree(new_level_folder)
    except:
        print('error removing folders, they will need to be removed manually')

print('processing: {}'.format(base_folder))
for level in os.listdir(base_folder):
    thread = threading.Thread(target=process_level, args=(level,))
    thread.start()
