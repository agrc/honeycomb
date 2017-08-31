#!/usr/bin/env python
# * coding: utf8 *
'''
honeycomb 🐝  # NOQA

Usage:
    honeycomb config init
    honeycomb config set --key <key> --value <value>
    honeycomb update-data
    [unimplemented] honeycomb start
    [unimplemented] honeycomb single <basemap>
    [unimplemented] honeycomb publish <basemap>
    [unimplemented] honeycomb config open
    [unimplemented] honeycomb config basemaps --add <basemap>
    [unimplemented] honeycomb config basemaps --remove <basemap>
Arguments:
    basemap                                                     The name of a registered base map.
Examples:
    honeycomb config init                                       Create a default config file.
    honeycomb config set --key sendEmails --value True          Write a value for a specific key to the config file.
    honeycomb update-data                                       Refreshes the data in the local FGDBs from SGID.

    honeycomb start                                             Kicks off the honeycomb process and loops through all of the base maps.
    honeycomb single Terrain                                    Builds a single base map.
    honeycomb publish Lite                                      Publishes a base map's associated MXD to ArcGIS Server (raster base maps only).
    honeycomb config open                                       Opens the config file in your default program for .json files.
    honeycomb config basemaps --add Night                       Adds the "Night" base map to the config.
    honeycomb config basemaps --remove Night                    Removes the "Night" base map from the config.
'''

from docopt import docopt
import sys
from . import config
from . import update_data


def main():
    args = docopt(__doc__, version='0.0.0')

    if args['config']:
        if args['init']:
            print('config file: {}'.format(config.create_default_config()))
        elif args['set'] and args['<key>'] and args['<value>']:
            print(config.set_config_prop(args['<key>'], args['<value>']))
    elif args['update-data']:
        update_data.main()


if __name__ == '__main__':
    sys.exit(main())
