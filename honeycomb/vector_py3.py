'''
vector_py3.py

A module for publishing vector tiles to ArcGIS Online. This requires running via the ArcGIS Pro python 3 environment.
e.g. propy vector_py3 addresspoints

Arguments:
1: name (this corresponds with the project folder name, project name and tile package file name)
2: summary (matches item summary in AGOL)
3: tags (comma-separated; matches tags in AGOL)
'''

import config
import sys
from os.path import join

import arcpy

BASE_FOLDER = config.get_config_value('vectorTilesFolder')


def main(base_map_name, summary, tags):
    print('building tiles for: ' + base_map_name)

    project_path = join(BASE_FOLDER, base_map_name)
    promap = arcpy.mp.ArcGISProject(join(project_path, base_map_name + '.aprx')).listMaps()[0]
    tile_package = join(project_path, base_map_name + '.vtpk')

    print('building tiles')
    if arcpy.Exists(tile_package):
        arcpy.management.Delete(tile_package)

    arcpy.management.CreateVectorTilePackage(promap, tile_package, 'ONLINE',
                                             tile_structure='INDEXED',
                                             min_cached_scale=295828763.795778,
                                             max_cached_scale=564.248588,
                                             summary=summary,
                                             tags=tags)

    print('publishing')
    arcpy.management.SharePackage(tile_package, '', '', summary, tags,
                                  credits='Utah AGRC',
                                  public='EVERYBODY',
                                  organization='EVERYBODY')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
