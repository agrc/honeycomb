#!/usr/bin/env python
# * coding: utf8 *
'''
config.py
A module that contains logic for reading and writing the config file
'''

from os import makedirs
from os.path import abspath
from os.path import dirname
from os.path import exists
from os.path import join
from json import dumps, loads


config_location = join(abspath(dirname(__file__)), '..', 'honeycomb-hive', 'config.json')


def create_default_config():
    try:
        makedirs(dirname(config_location))
    except:
        pass

    with open(config_location, 'w') as json_config_file:
        data = {
            'sendEmails': False,
            'basemaps': [],
            'notify': ['stdavis@utah.gov'],
            'baseFolder': None
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


def add_basemap(name):
    existing_basemaps = _get_config()['basemaps']
    new_basemaps = list(set(existing_basemaps + [name]))

    set_config_prop('basemaps', new_basemaps)

    return 'Added "{}" basemap. Current basemaps: {}'.format(name, ', '.join(new_basemaps))


def remove_basemap(name):
    basemaps = _get_config()['basemaps']

    try:
        basemaps.remove(name)
    except ValueError:
        return '"{}" is not a valid basemap name! Current basemaps: {}'.format(name, ', '.join(basemaps))

    set_config_prop('basemaps', basemaps)

    return 'Removed "{}" basemap. Current basemaps: {}'.format(name, ', '.join(basemaps))
