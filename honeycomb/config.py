#!/usr/bin/env python
# * coding: utf8 *
"""
config.py
A module that contains logic for reading and writing the config file
"""

from json import dumps, loads
from os import getenv, makedirs
from os.path import abspath, basename, dirname, exists, join

import requests
from google.cloud import storage

config_folder = abspath(join(abspath(dirname(__file__)), "..", "honeycomb-hive"))
config_location = join(config_folder, "config.json")
ags_connection_file = join(config_folder, "arcgisserver.ags")

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
            pool_connections=pool_threads, pool_maxsize=pool_threads, max_retries=3, pool_block=True
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
            "num_processes": 4,
            "sendEmails": False,
            "vectorBaseMaps": {},
            "vectorTilesFolder": "C:\\temp",
        }

        json_config_file.write(dumps(data, sort_keys=True, indent=2, separators=(",", ": ")))

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
        json_config_file.write(dumps(config, sort_keys=True, indent=2, separators=(",", ": ")))

    return message


def add_basemap(name, bucket=None, loop=False):
    basemaps = _get_config()["basemaps"]
    basemaps[name] = {"bucket": bucket, "loop": loop}

    set_config_prop("basemaps", basemaps)

    return 'Added "{}" basemap. Current basemaps: {}'.format(name, ", ".join(basemaps))


def remove_basemap(name):
    basemaps = _get_config()["basemaps"]

    try:
        basemaps.pop(name)
    except KeyError:
        return '"{}" is not a valid basemap name! Current basemaps: {}'.format(name, ", ".join(basemaps))

    set_config_prop("basemaps", basemaps)

    return 'Removed "{}" basemap. Current basemaps: {}'.format(name, ", ".join(basemaps))


def get_config_value(key):
    return _get_config()[key]


def is_dev():
    return _get_config()["configuration"] == "dev"


def get_ags_connection():
    """
    creates a server connection file if needed and returns the path to it
    """
    import arcpy  # : this is not imported at the top of the file to save it being imported in child processes in swarm.py

    if not exists(ags_connection_file):
        for variable in ["HONEYCOMB_AGS_SERVER", "HONEYCOMB_AGS_USERNAME", "HONEYCOMB_AGS_PASSWORD"]:
            if getenv(variable) is None:
                raise Exception("{} environment variable is not set!".format(variable))

        #: TODO: this tool is not available in Pro. I couldn't quickly find an alternative.
        arcpy.mapping.CreateGISServerConnectionFile(
            "PUBLISH_GIS_SERVICES",
            dirname(ags_connection_file),
            basename(ags_connection_file),
            getenv("HONEYCOMB_AGS_SERVER"),
            "ARCGIS_SERVER",
            username=getenv("HONEYCOMB_AGS_USERNAME"),
            password=getenv("HONEYCOMB_AGS_PASSWORD"),
        )

    return ags_connection_file


def get_basemap(name):
    basemaps = _get_config()["basemaps"]
    try:
        return basemaps[name]
    except KeyError:
        raise KeyError("Invalid basemap! Current basemaps: {}".format(", ".join(basemaps)))
