#!/usr/bin/env python
# * coding: utf8 *
'''
honeycomb 🐝  # NOQA

Usage:
    honeycomb config init
    honeycomb config set --key <key> --value <value>
    honeycomb config basemaps --add <basemap>
    honeycomb config basemaps --remove <basemap>
    honeycomb update-data
    [unimplemented] honeycomb single <basemap>
    [unimplemented] honeycomb start
    [unimplemented] honeycomb publish <basemap>
    [unimplemented] honeycomb config open
    [unimplemented] honeycomb config basemaps --add <basemap>
    [unimplemented] honeycomb config basemaps --remove <basemap>
Arguments:
    basemap                                                     The name of a registered base map (e.g. Terrain).
Examples:
    honeycomb config init                                       Create a default config file.
    honeycomb config set --key sendEmails --value True          Write a value for a specific key to the config file.
    honeycomb config basemaps --add Terrain                     Adds "Terrain" to the "basemaps" array in the config file.
    honeycomb config basemaps --remove Terrain                  Removes "Terrain" from the "basemaps" array in the config file.
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
        elif args['basemaps'] and args['<basemap>']:
            if args['--add']:
                print(config.add_basemap(args['<basemap>']))
            elif args['--remove']:
                print(config.remove_basemap(args['<basemap>']))
    elif args['update-data']:
        update_data.main()


if __name__ == '__main__':
    sys.exit(main())