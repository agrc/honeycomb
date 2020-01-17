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
from datetime import date
import sys
from os.path import join, dirname, realpath
import os

import arcpy
import arcgis
import pygsheets

BASE_FOLDER = config.get_config_value('vectorTilesFolder')
USERNAME = os.getenv('HONEYCOMB_AGOL_USERNAME')
PASSWORD = os.getenv('HONEYCOMB_AGOL_PASSWORD')

def main(id, base_map_name, summary, tags):
    print('building tiles for: ' + base_map_name)

    project_path = join(BASE_FOLDER, base_map_name)
    promap = arcpy.mp.ArcGISProject(join(project_path, base_map_name + '.aprx')).listMaps()[0]
    tile_package = join(project_path, base_map_name + '_temp' + '.vtpk')

    print('building package...')
    if arcpy.Exists(tile_package):
        arcpy.management.Delete(tile_package)

    arcpy.management.CreateVectorTilePackage(promap, tile_package, 'ONLINE',
                                             tile_structure='INDEXED',
                                             min_cached_scale=295828763.795778,
                                             max_cached_scale=564.248588,
                                             summary=summary,
                                             tags=tags)

    print('publishing new tile package item...')
    gis = arcgis.gis.GIS(username=USERNAME, password=PASSWORD)
    item = gis.content.add({}, data=tile_package)

    print('publishing new vector tiles service...')
    temp_item = item.publish()

    print('replacing production service...')
    prod_item = arcgis.gis.Item(gis, id)
    gis.content.replace_service(prod_item, temp_item)

    print('removing temporary items...')
    gis.content.delete_items([item, temp_item])

    print('vector tile package successfully built and published!')

    print('updating base maps spreadsheet')
    client = pygsheets.authorize(service_file=join(dirname(realpath(__file__)), 'deq-enviro-key.json'))
    base_maps_sheet = client.open_by_key('1XnncmhWrIjntlaMfQnMrlcCTyl9e2i-ztbvqryQYXDc')
    base_maps_worksheet = base_maps_sheet[0]

    today = date.today().strftime(r'%m/%d/%Y')
    results = base_maps_worksheet.find(base_map_name, matchEntireCell=True)
    cell = results[0]

    base_maps_worksheet.update_value((cell.row + 1, cell.col), today)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
