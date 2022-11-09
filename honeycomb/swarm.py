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
from p_tqdm import p_map
from google.api_core.retry import Retry
from google_crc32c import Checksum
from base64 import b64encode

from . import config, settings
from .messaging import send_email

storage_client = storage.Client(config.get_config_value('gcpProject'))

retry = Retry()

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
    upload_errors = []
    for file_path in row_folder.iterdir():
        try:
            column = str(int(file_path.name[1:-4], 16))
            #: set the content type explicitly in case it ever changes for a particular tile
            #: if you pass none then the content type of the existing blob object is used
            if file_path.suffix == '.png':
                content_type = 'image/png'
            else:
                content_type = 'image/jpeg'

            blob = bucket.blob(f'{name}/{level}/{column}/{row}')
            if blob.exists(retry=retry):
                blob.reload() #: required to get the checksum
                local_checksum = b64encode(Checksum(file_path.read_bytes()).digest()).decode('utf-8')
                if blob.crc32c != local_checksum:
                    blob.upload_from_filename(file_path, retry=retry, content_type=content_type)
            else:
                blob.upload_from_filename(file_path, retry=retry, content_type=content_type)
            file_path.unlink()
        except Exception:
            trace = traceback.format_exc()
            upload_errors.append(f'Uploading error. Level: {level}, row: {row}, column: {column}\n\n{trace}')
            print(trace)
    try:
        row_folder.rmdir()
    except Exception:
        trace = traceback.format_exc()
        send_email('Removing folder error. Level: {}'.format(level), trace)
        print(trace)

    if len(upload_errors) > 0:
        send_email('Uploading errors', '\n\n'.join(upload_errors))


def bust_discover_cache():
    giza_instance = config.get_config_value('gizaInstance')

    with requests.Session() as session:
        response = session.post('{}/login'.format(giza_instance),
                                data={'user': os.getenv('HONEYCOMB_GIZA_USERNAME'),
                                      'password': os.getenv('HONEYCOMB_GIZA_PASSWORD')})

        if response.status_code != 200:
            raise Exception('Login failed')

        response = session.get('{}/reset'.format(giza_instance))
