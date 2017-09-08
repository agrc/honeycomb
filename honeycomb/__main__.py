#!/usr/bin/env python
# * coding: utf8 *
'''
honeycomb 🐝  # NOQA

Usage:
    honeycomb config init
    honeycomb config set --key <key> --value <value>
    honeycomb config basemaps --add <basemap> [<bucket-name>] [<image-type>] [--loop]
    honeycomb config basemaps --remove <basemap>
    honeycomb config open
    honeycomb update-data
    honeycomb loop
    honeycomb <basemap> [--missing-only] [--skip-update] [--skip-test]
    [unimplemented] honeycomb publish <basemap>

Arguments:
    -h --help               Show this screen.
    basemap                 The name of a registered base map (e.g. Terrain).
    bucket-name             The name of the GCP bucket were you want the tiles to be pushed to.
    image-type              The output image type of the cache tiles ("jpeg" or "png")
    --loop                  Include the base map in the loop command.
    --missing-only          Only missing tiles are generated.
    --skip-update           Skip update vector data from SGID.
    --skip-test             Skip running a test cache.

Examples:
    honeycomb config init                                       Create a default config file.
    honeycomb config set --key sendEmails --value True          Write a value for a specific key to the config file.
    honeycomb config basemaps --add Terrain                     Adds "Terrain" to the "basemaps" array in the config file.
    honeycomb config basemaps --remove Terrain                  Removes "Terrain" from the "basemaps" array in the config file.
    honeycomb config open                                       Opens the config file in your default editor.
    honeycomb update-data                                       Refreshes the data in the local FGDBs from SGID.
    honeycomb loop                                              Kicks off the honeycomb process and loops through all of the base maps.
    honeycomb Terrain                                           Builds a single base map and pushes to GCP.
    honeycomb publish Lite                                      Publishes a base map's associated MXD to ArcGIS Server (raster base maps only).
'''

from . import config
from . import update_data
from .swarm import swarm
from .worker_bee import WorkerBee
from docopt import docopt
from os import startfile
import sys


def main():
    args = docopt(__doc__, version='0.0.0')

    def cache(basemap):
        WorkerBee(basemap, args['--missing-only'], args['--skip-update'], args['--skip-test'])

        def prompt_recache():
            return raw_input('Caching complete. Publish to production (P) or recache (R)? ') != 'P'

        recache = prompt_recache()
        while recache:
            # WorkerBee(basemap, False, True, True)
            recache = prompt_recache()

        basemap_info = config.get_basemap(basemap)
        swarm(basemap, basemap_info['bucket'], basemap_info['image_type'])

    if args['config']:
        if args['init']:
            print('config file: {}'.format(config.create_default_config()))
        elif args['set'] and args['<key>'] and args['<value>']:
            print(config.set_config_prop(args['<key>'], args['<value>']))
        elif args['basemaps'] and args['<basemap>']:
            if args['--add']:
                print(config.add_basemap(args['<basemap>'], args['<bucket-name>'], args['<image-type>'], args['--loop']))
            elif args['--remove']:
                print(config.remove_basemap(args['<basemap>']))
        elif args['open']:
            startfile(config.config_location)
    elif args['update-data']:
        update_data.main()
    elif args['<basemap>']:
        cache(args['<basemap>'])
    elif args['loop']:
        stop = False
        basemaps = config.get_config_value('basemaps')
        while not stop:
            for basemap in basemaps.keys():
                action = raw_input('cache {} (C), skip to the next base map (S) or exit (E)? '.format(basemap))
                if action == 'C':
                    cache(basemap)
                elif action == 'S':
                    continue
                else:
                    stop = True
                    break


if __name__ == '__main__':
    sys.exit(main())
