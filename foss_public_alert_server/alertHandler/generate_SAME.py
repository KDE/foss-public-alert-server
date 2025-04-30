# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

# note: marine SAME codes are symlinked to the marine zone UGCs and as such are created by generate_UGC.py

import json
import os
import shapefile

DATE = '18mr25'
COUNTY_URL = f'https://www.weather.gov/source/gis/Shapefiles/County/cs{DATE}.zip'
STATE_URL = f'https://www.weather.gov/source/gis/Shapefiles/County/s_{DATE}.zip'
FOLDER_NAME = 'data/SAME/'

def write_to_file(geojson, name):
    path = os.path.join(os.path.dirname(__file__), FOLDER_NAME, name + '.geojson')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(geojson))
        f.close()

def return_county_same(polygon):
    """return county SAME code"""
    return f'{polygon['properties']['AREA_SAME']}'

def return_state_same(polygon):
    """return state SAME code"""
    return f'0{polygon['properties']['FIPS']}000'

datasets = {'county': {'url': COUNTY_URL, 'namefunc': return_county_same}, 'state': {'url': STATE_URL, 'namefunc': return_state_same}}

for dataset_name, dataset_attributes in datasets.items():
    # read url from dataset entry and create the collection object
    reader = shapefile.Reader(dataset_attributes['url'])
    collection = reader.shapeRecords()
    for region in collection.__geo_interface__['features']:
        # write every shape to a geojson file named by a function using the shape's attributes
        write_to_file(region, dataset_attributes['namefunc'](region))
