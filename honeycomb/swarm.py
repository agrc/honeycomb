#!/usr/bin/env python
# * coding: utf8 *
'''
swarm.py

A module that contains code for etl-ing tiles into WMTS format and uploading to GCP.
'''

import glob
import os
import shutil
import subprocess
import traceback
from functools import partial

import requests
from multiprocess import Pool

from . import config, settings
from .messaging import send_email


def swarm(name, bucket, image_type):
    print('processing: {}'.format(name))

    etl(name)
    column_folders = glob.iglob('{}/**/*'.format(os.path.join(settings.CACHE_DIR, name + '_GCS')))

    pool = Pool(config.get_config_value('num_processes'))
    pool.map(partial(upload, bucket, image_type), column_folders)
    pool.close()

    bust_discover_cache()


def etl(name):
    '''
    copies all tiles into WMTS format as a sibling folder to the AGS cache folder
    returns a list of all of the column folders
    '''
    new_folder = os.path.join(settings.CACHE_DIR, name + '_GCS')
    base_folder = os.path.join(settings.CACHE_DIR, name, 'Layers', '_alllayers')

    for level in os.listdir(base_folder):
        print('etl-ing level: {}'.format(level))
        new_level = str(int(level[1:]))
        new_level_folder = os.path.join(new_folder, new_level)
        if not os.path.exists(new_level_folder):
            os.makedirs(new_level_folder)

        print('globbing')
        paths = glob.iglob('{}/{}/**/*.*[!.lock]'.format(base_folder, level))

        print('processing folders')
        for file_path in paths:
            parts = file_path.split(os.path.sep)[-2:]
            row = str(int(parts[0][1:], 16))
            column = str(int(parts[1][1:-4], 16))
            column_folder = os.path.join(new_level_folder, column)
            if not os.path.exists(column_folder):
                os.mkdir(column_folder)

            shutil.copy(os.path.join(base_folder, level, file_path), os.path.join(column_folder, row))

        print('cleaning up AGS tiles')

        shutil.rmtree(os.path.join(base_folder, level))


def upload(bucket, image_type, column_folder):
    '''
    upload all tile in folder to GCP, then clean up the folder
    '''
    print('uploading: ' + column_folder)
    content_type = 'image/{}'.format(image_type)
    level = os.path.basename(os.path.dirname(column_folder))

    try:
        subprocess.check_call([
            'gsutil',
            '-m',
            '-h',
            'Content-Type:' + content_type,
            'rsync',
            '-a',
            'public-read',
            '-r',  #: recursive
            '-c',  #: force hashing for change detection
            '-d',  #: delete extra files in destination not found in source
            column_folder,
            'gs://{}/{}/{}'.format(bucket, level, os.path.basename(column_folder))
        ], shell=True)

        try:
            print('removing local folder')
            shutil.rmtree(column_folder)
        except Exception:
            print('error removing folders, they will need to be removed manually')
    except Exception:
        trace = traceback.format_exc()
        send_email('Uploading error. Level: {}'.format(level), trace)
        print(trace)


def bust_discover_cache():
    giza_instance = config.get_config_value('gizaInstance')

    with requests.Session() as session:
        response = session.post('{}/login'.format(giza_instance),
                                data={'user': os.getenv('HONEYCOMB_GIZA_USERNAME'),
                                      'password': os.getenv('HONEYCOMB_GIZA_PASSWORD')})

        if response.status_code != 200:
            raise Exception('Login failed')

        response = session.get('{}/reset'.format(giza_instance))
