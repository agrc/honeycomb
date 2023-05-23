#!/usr/bin/env python
# * coding: utf8 *
'''
honeycomb 🐝  # NOQA

Usage:
    honeycomb config init
    honeycomb config set --key <key> --value <value>
    honeycomb config basemaps --add <basemap> [<bucket-name>] [--loop]
    honeycomb config basemaps --remove <basemap>
    honeycomb config open
    honeycomb update-data [--static-only] [--sgid-only]
    honeycomb loop
    honeycomb upload <basemap>
    honeycomb stats
    honeycomb vector <basemap>
    honeycomb vector-all
    honeycomb <basemap> [--missing-only] [--skip-update] [--skip-test] [--spot <path>] [--levels <levels>]
    honeycomb publish <basemap>

Arguments:
    -h --help               Show this screen.
    basemap                 The name of a registered base map (e.g. Terrain).
    bucket-name             The name of the GCP bucket were you want the tiles to be pushed to.
    --loop                  Include the base map in the loop command.
    --missing-only          Only missing tiles are generated.
    --skip-update           Skip update vector data from SGID.
    --skip-test             Skip running a test cache.
    --spot <path>           Cache only a specific extent. <path> is a path to a polygon feature class.
    --levels <levels>       Cache only specific levels
    --static-only           Copy static data from the SHARE to your local machine.
    --sgid-only             Copy vector data from the SGID to your local machine.

Examples:
    honeycomb config init                                       Create a default config file.
    honeycomb config set --key sendEmails --value True          Write a value for a specific key to the config file.
    honeycomb config basemaps --add Terrain                     Adds "Terrain" to the "basemaps" array in the config file.
    honeycomb config basemaps --remove Terrain                  Removes "Terrain" from the "basemaps" array in the config file.
    honeycomb config open                                       Opens the config file in your default editor.
    honeycomb update-data                                       Refreshes the data on your computer from SGID and the static data on the share.
    honeycomb update-data --static-only                         Refreshes the data on your computer from the static data on the share only.
    honeycomb loop                                              Kicks off the honeycomb process and loops through all of the base maps.
    honeycomb upload Terrain                                    ETLs and uploads the tiles for the Terrain cache to GCP.
    honeycomb Terrain                                           Builds a single base map and pushes to GCP.
    honeycomb Terrain --skip-update                             Builds a single base map (skipping data update) and pushes to GCP.
    honeycomb Terrain --skip-test --spot C:\\\\test.gdb\\extent Builds a single base map (skipping test and for a specific extent) and pushes to GCP.
    honeycomb Terrain --levels 5-7                              Builds a single base map for levels 5, 6 & 7 and pushes to GCP.
    honeycomb publish Lite                                      Publishes a base map's associated MXD to ArcGIS Server (raster base maps only).
    honeycomb vector UtahAddressPoints                          Builds a new vector tile package and uploads to AGOL.
    honeycomb vector-all                                        Builds all of the vector tile packages in the config and uploads to AGOL.
'''

import sys
from os import startfile

from docopt import docopt

from . import config, update_data, stats, vector
from .publish import publish
from .swarm import swarm
from .worker_bee import WorkerBee


def main():
    args = docopt(__doc__, version='1.1.1')

    def cache(basemap):
        stats.record_start(basemap, 'cache')
        WorkerBee(basemap, args['--missing-only'], args['--skip-update'], args['--skip-test'], args['--spot'], args['--levels'])
        stats.record_finish(basemap, 'cache')

        # def prompt_recache():
        #     return raw_input('Caching complete. Publish to production (P) or recache (R)? ') != 'P'
        #
        # recache = prompt_recache()
        # while recache:
        #     WorkerBee(basemap, False, True, True)
        #     recache = prompt_recache()

        upload(basemap)

    def upload(basemap):
        basemap_info = config.get_basemap(basemap)
        stats.record_start(basemap, 'upload')
        swarm(basemap, basemap_info['bucket'])
        stats.record_finish(basemap, 'upload')

    if args['config']:
        if args['init']:
            print('config file: {}'.format(config.create_default_config()))
        elif args['set'] and args['<key>'] and args['<value>']:
            print(config.set_config_prop(args['<key>'], args['<value>']))
        elif args['basemaps'] and args['<basemap>']:
            if args['--add']:
                print(config.add_basemap(args['<basemap>'], args['<bucket-name>'], args['--loop']))
            elif args['--remove']:
                print(config.remove_basemap(args['<basemap>']))
        elif args['open']:
            startfile(config.config_location)
    elif args['update-data']:
        update_data.main(args['--static-only'], args['--sgid-only'])
    elif args['upload'] and args['<basemap>']:
        upload(args['<basemap>'])
    elif args['loop']:
        stop = False
        basemaps = config.get_config_value('basemaps')
        while not stop:
            for basemap in [key for key in list(basemaps.keys()) if basemaps[key]['loop']]:
                action = input('cache {} (C), skip to the next base map (S) or exit (E)? '.format(basemap))
                if action == 'C':
                    cache(basemap)
                elif action == 'S':
                    continue
                else:
                    stop = True
                    break
    elif args['publish']:
        publish(args['<basemap>'])
    elif args['vector']:
        basemap = args['<basemap>']
        vector_basemaps = config.get_config_value('vectorBaseMaps')

        stats.record_start(basemap, 'cache')
        vector.main(basemap, vector_basemaps[basemap])
        stats.record_finish(basemap, 'cache')
    elif args['vector-all']:
        vector_basemaps = config.get_config_value('vectorBaseMaps')
        for basemap in [key for key in list(vector_basemaps.keys())]:
            stats.record_start(basemap, 'cache')
            vector.main(basemap, vector_basemaps[basemap])
            stats.record_finish(basemap, 'cache')
    elif args['<basemap>']:
        cache(args['<basemap>'])
    elif args['stats']:
        stats.print_stats()


if __name__ == '__main__':
    sys.exit(main())
