#!/usr/bin/env python
# * coding: utf8 *
'''
config.py
A module that contains logic for reading and writing the config file
'''

from json import dumps, loads
from os import makedirs, getenv
from os.path import abspath, dirname, exists, join, basename
import arcpy


config_folder = join(abspath(dirname(__file__)), '..', 'honeycomb-hive')
config_location = join(config_folder, 'config.json')
ags_connection_file = join(config_folder, 'arcgisserver.ags')


def create_default_config():
    try:
        makedirs(dirname(config_location))
    except:
        pass

    with open(config_location, 'w') as json_config_file:
        data = {
            'sendEmails': False,
            'basemaps': {},
            'notify': ['stdavis@utah.gov'],
            'configuration': 'dev'
        }

        json_config_file.write(dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

        return abspath(json_config_file.name)


def _get_config():
    #: write default config if the file does not exist
    if not exists(config_location):
        create_default_config()

    with open(config_location, 'r') as json_config_file:
        return loads(json_config_file.read())


def set_config_prop(key, value):
    config = _get_config()

    if key not in config:
        raise ValueError('{} not found in config.'.format(key))

    config[key] = value
    message = 'Set {} to {}'.format(key, value)

    with open(config_location, 'w') as json_config_file:
        json_config_file.write(dumps(config, sort_keys=True, indent=2, separators=(',', ': ')))

    return message


def add_basemap(name, bucket=None, image_type=None, loop=False):
    basemaps = _get_config()['basemaps']
    basemaps[name] = {
        'bucket': bucket,
        'image_type': image_type,
        'loop': loop
    }

    set_config_prop('basemaps', basemaps)

    return 'Added "{}" basemap. Current basemaps: {}'.format(name, ', '.join(basemaps))


def remove_basemap(name):
    basemaps = _get_config()['basemaps']

    try:
        basemaps.pop(name)
    except KeyError:
        return '"{}" is not a valid basemap name! Current basemaps: {}'.format(name, ', '.join(basemaps))

    set_config_prop('basemaps', basemaps)

    return 'Removed "{}" basemap. Current basemaps: {}'.format(name, ', '.join(basemaps))


def get_config_value(key):
    return _get_config()[key]


def is_dev():
    return _get_config()['configuration'] == 'dev'


def get_ags_connection():
    '''
    creates a server connection file if needed and returns the path to it
    '''

    if not exists(ags_connection_file):
        for variable in ['HONEYCOMB_AGS_SERVER', 'HONEYCOMB_AGS_USERNAME', 'HONEYCOMB_AGS_PASSWORD']:
            if getenv(variable) is None:
                raise Exception('{} environment variable is not set!'.format(variable))

        arcpy.mapping.CreateGISServerConnectionFile('PUBLISH_GIS_SERVICES',
                                                    dirname(ags_connection_file),
                                                    basename(ags_connection_file),
                                                    getenv('HONEYCOMB_AGS_SERVER'),
                                                    'ARCGIS_SERVER',
                                                    username=getenv('HONEYCOMB_AGS_USERNAME'),
                                                    password=getenv('HONEYCOMB_AGS_PASSWORD'))

    return ags_connection_file.replace('.ags', '')


def get_basemap(name):
    basemaps = _get_config()['basemaps']
    try:
        return basemaps[name]
    except KeyError:
        raise KeyError('Invalid basemap! Current basemaps: {}'.format(', '.join(basemaps)))
