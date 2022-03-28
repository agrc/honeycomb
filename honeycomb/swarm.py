#!/usr/bin/env python
# * coding: utf8 *
'''
swarm.py

A module that contains code for etl-ing tiles into WMTS format and uploading to GCP.
'''

import os
import traceback
from functools import partial
from pathlib import Path

import requests
from google.cloud import storage
from google.oauth2 import service_account
from p_tqdm import p_map

from . import config, settings
from .messaging import send_email

credentials = service_account.Credentials.from_service_account_file(Path(__file__).parent / 'service-account.json')
storage_client = storage.Client(config.get_config_value('gcpProject'), credentials)

def swarm(name, bucket_name):
    '''
    copies all tiles into WMTS format as a sibling folder to the AGS cache folder
    returns a list of all of the column folders
    '''
    base_folder = Path(settings.CACHE_DIR) / name / name / '_alllayers'

    for level_folder in sorted(base_folder.iterdir()):
        level = str(int(level_folder.name[1:]))
        print('uploading level: {}'.format(level))

        row_folders = [folder for folder in level_folder.iterdir()]
        if len(row_folders) > 0:
            p_map(partial(process_row_folder, name, bucket_name, level), row_folders)

    bust_discover_cache()
    send_email('honeycomb update', '{} has been pushed to production'.format(name))


def process_row_folder(name, bucket_name, level, row_folder):
    bucket = storage_client.bucket(bucket_name)
    row = str(int(row_folder.name[1:], 16))
    try:
        for file_path in row_folder.iterdir():
            column = str(int(file_path.name[1:-4], 16))

            blob = bucket.blob(f'{name}/{level}/{column}/{row}')
            blob.upload_from_filename(file_path)
            file_path.unlink()
        row_folder.rmdir()
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
