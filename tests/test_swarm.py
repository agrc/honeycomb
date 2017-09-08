#!/usr/bin/env python
# * coding: utf8 *
'''
test_swarm.py

A module that contains tests for the swarm module
'''

from . import conftest
from honeycomb import swarm, settings
from mock import patch
from os import walk
from os.path import join, exists
import shutil


@patch('honeycomb.swarm.etl', return_value=[])
def test_swarm(mock):
    swarm.swarm('Terrain', 'bucket', 'png')

    mock.assert_called_once()


def test_etl():
    service = 'JPG_Service'
    shutil.copytree(join(conftest.test_data_folder, service), join(conftest.temp_folder, service))

    settings.CACHE_DIR = conftest.temp_folder

    swarm.etl(service)

    def get_files(folder):
        entries = []
        for root, directories, files in walk(folder):
            files.append([directories, files])

        return entries

    etled_files = get_files(join(conftest.temp_folder, service + '_GCS'))
    expected_files = get_files(join(conftest.test_data_folder, service + '_GCS'))

    assert etled_files == expected_files


@patch('honeycomb.swarm.subprocess.check_call')
def test_upload(check_call_mock):
    column_folder = join(conftest.temp_folder, 'JPG_Service', '5', '4')
    shutil.copytree(join(conftest.test_data_folder, 'JPG_Service_GCS', '5', '4'), column_folder)

    swarm.upload('bucket', 'png', column_folder)

    check_call_mock.assert_called_once()
    assert not exists(column_folder)
