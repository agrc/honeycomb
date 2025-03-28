#!/usr/bin/env python
# * coding: utf8 *
"""
config.py
A module that contains logic for reading and writing the config file
"""

from json import dumps, loads
from os import makedirs
from os.path import abspath, dirname, exists, join

import requests
from google.cloud import storage

config_folder = abspath(join(abspath(dirname(__file__)), "..", "honeycomb-hive"))
config_location = join(config_folder, "config.json")

#: do this on load so that stats.py can use it
try:
    makedirs(dirname(config_location))
except Exception:
    pass

storage_client = None


pool_threads = 100


def get_storage_client():
    global storage_client
    if storage_client is None:
        storage_client = storage.Client(get_config_value("gcpProject"))
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=pool_threads,
            pool_maxsize=pool_threads,
            max_retries=3,
            pool_block=True,
        )
        storage_client._http.mount("https://", adapter)
        storage_client._http._auth_request.session.mount("https://", adapter)

    return storage_client


def create_default_config():
    with open(config_location, "w") as json_config_file:
        data = {
            "basemaps": {},
            "configuration": "dev",
            "gcpProject": "",
            "gizaInstance": "https://discover.agrc.utah.gov",
            "mxdFolder": "C:\\temp",
            "notify": ["stdavis@utah.gov"],
            "sendEmails": False,
            "vectorBaseMaps": {},
            "vectorTilesFolder": "C:\\temp",
        }

        json_config_file.write(
            dumps(data, sort_keys=True, indent=2, separators=(",", ": "))
        )

        return abspath(json_config_file.name)


def _get_config():
    #: write default config if the file does not exist
    if not exists(config_location):
        create_default_config()

    with open(config_location, "r") as json_config_file:
        return loads(json_config_file.read())


def set_config_prop(key, value):
    config = _get_config()

    if key not in config:
        raise ValueError("{} not found in config.".format(key))

    config[key] = value
    message = "Set {} to {}".format(key, value)

    with open(config_location, "w") as json_config_file:
        json_config_file.write(
            dumps(config, sort_keys=True, indent=2, separators=(",", ": "))
        )

    return message


def add_basemap(name, bucket=None, loop=False, imageType="jpeg"):
    basemaps = _get_config()["basemaps"]
    basemaps[name] = {"bucket": bucket, "loop": loop, "imageType": imageType}

    set_config_prop("basemaps", basemaps)

    return 'Added "{}" basemap. Current basemaps: {}'.format(name, ", ".join(basemaps))


def remove_basemap(name):
    basemaps = _get_config()["basemaps"]

    try:
        basemaps.pop(name)
    except KeyError:
        return '"{}" is not a valid basemap name! Current basemaps: {}'.format(
            name, ", ".join(basemaps)
        )

    set_config_prop("basemaps", basemaps)

    return 'Removed "{}" basemap. Current basemaps: {}'.format(
        name, ", ".join(basemaps)
    )


def get_config_value(key):
    return _get_config()[key]


def is_dev():
    return _get_config()["configuration"] == "dev"


def get_basemap(name):
    basemaps = _get_config()["basemaps"]
    try:
        return basemaps[name]
    except KeyError:
        raise KeyError(
            "Invalid basemap! Current basemaps: {}".format(", ".join(basemaps))
        )
