# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import shapefile

FOLDER_NAME = "data/"

def write_to_file(geojson, name):
    path = os.path.join(os.path.dirname(__file__), FOLDER_NAME, name + '.geojson')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(geojson))
        f.close()

# this defines all the datasets with the link, name attribute and folder
datasets = {'city_113': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/city_113.shp(utf8).zip', 'name': 'COUNTYCODE', 'folder': 'Taiwan_Geocode_113/'},
            'city_112': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/city_112.shp(utf8)v1.zip', 'name': 'NCITY_112', 'folder': 'Taiwan_Geocode_112/'},
            'town_113': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/town_113(utf8).zip', 'name': 'TOWNCODE', 'folder': 'Taiwan_Geocode_113/'},
            'town_107': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/town_107(utf8).zip', 'name': 'TOWNCODE', 'folder': 'Taiwan_Geocode_107/'},
            'town_103': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/town_103.shp(utf8)v2.zip', 'name': 'nTown103', 'folder': 'Taiwan_Geocode_103/'},
            'village_113': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/vallige_113(utf8).zip', 'name': 'VILLCODE', 'folder': 'Taiwan_Geocode_113/'},
            'village_107': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/vallige_107(utf8).zip', 'name': 'VILLCODE', 'folder': 'Taiwan_Geocode_107/'},
            'village_106': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/village_106.shp(utf8).zip', 'name': 'nVill106', 'folder': 'Taiwan_Geocode_106/'},
            'village_103': {'url': 'https://alerts.ncdr.nat.gov.tw/Document/village_103.shp(utf8)v2.zip', 'name': 'nVill103','folder': 'Taiwan_Geocode_103/'},}

for dataset_name, dataset_attributes in datasets.items():
    reader = shapefile.Reader(dataset_attributes['url'])
    print(dataset_name, "downloaded")
    collection = reader.shapeRecords()
    for region in collection.__geo_interface__['features']:
        write_to_file(region, dataset_attributes['folder'] + region['properties'][dataset_attributes['name']])
