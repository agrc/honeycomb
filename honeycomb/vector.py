'''
vector.py

A module for publishing vector tiles to ArcGIS Online.

Arguments:
1: name (this corresponds with the project folder name, project name and tile package file name)
2: summary (matches item summary in AGOL)
3: tags (comma-separated; matches tags in AGOL)
'''

from . import config
from datetime import date
from os.path import join, dirname, realpath
import os

import arcpy
import arcgis
import pygsheets
import google.auth

BASE_FOLDER = config.get_config_value('vectorTilesFolder')
USERNAME = os.getenv('HONEYCOMB_AGOL_USERNAME')
PASSWORD = os.getenv('HONEYCOMB_AGOL_PASSWORD')

def main(base_map_name, config):
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
                                             summary=config['summary'],
                                             tags=config['tags'])

    print('publishing new tile package item...')
    gis = arcgis.gis.GIS(username=USERNAME, password=PASSWORD)
    item = gis.content.add({}, data=tile_package)

    print('publishing new vector tiles service...')
    temp_item = item.publish()

    print('replacing production service...')
    prod_item = arcgis.gis.Item(gis, config['id'])
    gis.content.replace_service(prod_item, temp_item)

    print('removing temporary items...')
    gis.content.delete_items([item, temp_item])

    print('vector tile package successfully built and published!')

    print('updating base maps spreadsheet')
    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client = pygsheets.authorize(custom_credentials=credentials)
    base_maps_sheet = client.open_by_key('1XnncmhWrIjntlaMfQnMrlcCTyl9e2i-ztbvqryQYXDc')
    base_maps_worksheet = base_maps_sheet[0]

    today = date.today().strftime(r'%m/%d/%Y')
    results = base_maps_worksheet.find(base_map_name, includeFormulas=True)
    cell = results[0]

    base_maps_worksheet.update_value((cell.row + 1, cell.col), today)
