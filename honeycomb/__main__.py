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
    honeycomb upload <basemap>
    honeycomb <basemap> [--missing-only] [--skip-update] [--skip-test] [--spot <path>] [--levels <levels>]
    honeycomb publish <basemap>
    honeycomb vector <basemap>

Arguments:
    -h --help               Show this screen.
    basemap                 The name of a registered base map (e.g. Terrain).
    bucket-name             The name of the GCP bucket were you want the tiles to be pushed to.
    image-type              The output image type of the cache tiles ("jpeg" or "png")
    --loop                  Include the base map in the loop command.
    --missing-only          Only missing tiles are generated.
    --skip-update           Skip update vector data from SGID.
    --skip-test             Skip running a test cache.
    --spot <path>           Cache only a specific extent. <path> is a path to a polygon feature class.
    --levels <levels>       Cache only specific levels

Examples:
    honeycomb config init                                       Create a default config file.
    honeycomb config set --key sendEmails --value True          Write a value for a specific key to the config file.
    honeycomb config basemaps --add Terrain                     Adds "Terrain" to the "basemaps" array in the config file.
    honeycomb config basemaps --remove Terrain                  Removes "Terrain" from the "basemaps" array in the config file.
    honeycomb config open                                       Opens the config file in your default editor.
    honeycomb update-data                                       Refreshes the data in the local FGDBs from SGID.
    honeycomb loop                                              Kicks off the honeycomb process and loops through all of the base maps.
    honeycomb upload Terrain                                    ETLs and uploads the tiles for the Terrain cache to GCP.
    honeycomb Terrain                                           Builds a single base map and pushes to GCP.
    honeycomb Terrain --skip-update                             Builds a single base map (skipping data update) and pushes to GCP.
    honeycomb Terrain --skip-test --spot C:\\\\test.gdb\\extent Builds a single base map (skipping test and for a specific extent) and pushes to GCP.
    honeycomb Terrain --levels 5-7                              Builds a single base map for levels 5, 6 & 7 and pushes to GCP.
    honeycomb publish Lite                                      Publishes a base map's associated MXD to ArcGIS Server (raster base maps only).
    honeycomb vector UtahAddressPoints                          Builds a new vector tile package and uploads to AGOL.
'''

import subprocess
import sys
from os import path, startfile

from docopt import docopt

from . import config, update_data
from .publish import publish
from .swarm import swarm
from .worker_bee import WorkerBee


def main():
    args = docopt(__doc__, version='1.1.1')

    def cache(basemap):
        WorkerBee(basemap, args['--missing-only'], args['--skip-update'], args['--skip-test'], args['--spot'], args['--levels'])

        def prompt_recache():
            return raw_input('Caching complete. Publish to production (P) or recache (R)? ') != 'P'

        recache = prompt_recache()
        while recache:
            WorkerBee(basemap, False, True, True)
            recache = prompt_recache()

        upload(basemap)

    def upload(basemap):
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
    elif args['upload'] and args['<basemap>']:
        upload(args['<basemap>'])
    elif args['loop']:
        stop = False
        basemaps = config.get_config_value('basemaps')
        while not stop:
            for basemap in [key for key in basemaps.keys() if basemaps[key]['loop']]:
                action = raw_input('cache {} (C), skip to the next base map (S) or exit (E)? '.format(basemap))
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
        vector_module = path.join(path.abspath(path.dirname(__file__)), 'vector_py3.py')
        summary = vector_basemaps[basemap]['summary']
        tags = vector_basemaps[basemap]['tags']

        print('building and publishing: ' + basemap)
        print('summary: ' + summary)
        print('tags: ' + tags)

        command = ['propy', '-E', vector_module, basemap, summary, tags]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()

        if output:
            print(output)
        if error:
            print(error)
    elif args['<basemap>']:
        cache(args['<basemap>'])


if __name__ == '__main__':
    sys.exit(main())
