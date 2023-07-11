#!/usr/bin/env python
# * coding: utf8 *
"""
test_swarm.py

A module that contains tests for the swarm module
"""

import shutil
from os import walk
from os.path import exists, join

import requests_mock
from honeycomb import config, settings, swarm
from mock import patch
from pytest import raises

from . import conftest

giza_instance = config.get_config_value("gizaInstance")
login_path = "{}/login".format(giza_instance)


def mock_success(requests_mock):
    requests_mock.post(login_path, status_code=200)
    requests_mock.get("{}/reset".format(giza_instance), status_code=200)


@patch("honeycomb.swarm.etl")
@patch("honeycomb.swarm.upload")
@requests_mock.mock()
def test_swarm(upload_mock, etl_mock, requests_mock):
    mock_success(requests_mock)
    swarm.swarm("Terrain", "bucket", "png")

    etl_mock.assert_called_once()


def test_etl(benchmark):
    service = "JPG_Service"
    shutil.copytree(join(conftest.test_data_folder, service), join(conftest.temp_folder, service))

    settings.CACHE_DIR = conftest.temp_folder

    benchmark(swarm.etl, service)

    def get_files(folder):
        entries = []
        for root, directories, files in walk(folder):
            files.append([directories, files])

        return entries

    etled_files = get_files(join(conftest.temp_folder, service + "_GCS"))
    expected_files = get_files(join(conftest.test_data_folder, service + "_GCS"))

    assert etled_files == expected_files


@patch("honeycomb.swarm.subprocess.check_call")
def test_upload(check_call_mock):
    column_folder = join(conftest.temp_folder, "JPG_Service", "5", "4")
    shutil.copytree(join(conftest.test_data_folder, "JPG_Service_GCS", "5", "4"), column_folder)

    swarm.upload("bucket", "png", column_folder)

    check_call_mock.assert_called_once()
    assert not exists(column_folder)


@requests_mock.mock()
def test_bust_discover_cache(mock):
    mock_success(mock)

    swarm.bust_discover_cache()

    mock.post(login_path, status_code=304)

    with raises(Exception):
        swarm.bust_discover_cache()
