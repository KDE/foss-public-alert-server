# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import csv
from io import StringIO
import requests
import shapefile

# note: these two date variables may need to be updated from time to time in the case of new releases with a later valid date.
CURRENT_DATE = '18mr25'
LOOKUP_DATE = '14fe25'

UGC_FOLDER_NAME = 'data/UGC/'
SAME_FOLDER_NAME = 'data/SAME/'

lookup_sequence = ['SSALPHA', 'SSNUM', 'ABBNAME', 'AREANAME']
lookup_text = requests.get(f'https://www.weather.gov/source/gis/Shapefiles/WSOM/marst{LOOKUP_DATE}.txt', timeout=10).text # check https://www.weather.gov/gis/EasNWR for updates
lookup_data = list(csv.DictReader(StringIO(lookup_text), fieldnames=lookup_sequence, delimiter='|'))

COASTAL_LINK = f'https://www.weather.gov/source/gis/Shapefiles/WSOM/mz{CURRENT_DATE}.zip'  # check https://www.weather.gov/gis/MarineZones for updates
OFFSHORE_LINK = f'https://www.weather.gov/source/gis/Shapefiles/WSOM/oz{CURRENT_DATE}.zip' # check https://www.weather.gov/gis/MarineZones for updates
ZONES_LINK = f'https://www.weather.gov/source/gis/Shapefiles/WSOM/z_{CURRENT_DATE}.zip'    # check https://www.weather.gov/gis/PublicZones for updates
COUNTY_LINK = f'https://www.weather.gov/source/gis/Shapefiles/County/c_{CURRENT_DATE}.zip' # check https://www.weather.gov/gis/Counties for updates

def write_to_file(geojson, name):
    path = os.path.join(os.path.dirname(__file__), UGC_FOLDER_NAME, name + '.geojson')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(geojson))
        f.close()

def return_simple_ugc(polygon):
    '''dummy function to return complete UGC from coastal and offshore datasets'''
    return polygon['properties']['ID']

def return_zone_ugc(polygon):
    '''assembles UGC in ssZnnn format, where ss is the state code and zzz is the zone number'''
    return f'{polygon['properties']['STATE']}Z{polygon['properties']['ZONE']}'

def return_county_ugc(polygon):
    '''assembles UGC in ssCnnn format, where ss is the state code and nnn is the FIPS number.'''
    return f'{polygon['properties']['STATE']}C{polygon['properties']['FIPS'][2:]}'

def return_marine_same(row, polygon):
    '''returns a marine SAME code for a given marine UGC'''
    return f'0{row['SSNUM']}{polygon['properties']['ID'][3:]}'

def return_county_same(polygon):
    '''returns a county SAME code for a given county UGC'''
    return f'0{polygon['properties']['FIPS']}'

def symlink_same(same, ugc):
    '''symlink a given SAME code to a UGC'''
    dest = os.path.join(SAME_FOLDER_NAME, f"{same}.geojson")
    if os.path.isfile(dest):
        os.remove(dest)
    src = os.path.join(os.path.relpath(UGC_FOLDER_NAME, SAME_FOLDER_NAME), f"{ugc}.geojson")
    os.symlink(src, dest)

datasets = {'coastal': {'url': COASTAL_LINK, 'namefunc': return_simple_ugc},
            'offshore': {'url': OFFSHORE_LINK, 'namefunc': return_simple_ugc},
            'zones': {'url': ZONES_LINK, 'namefunc': return_zone_ugc},
            'county': {'url': COUNTY_LINK, 'namefunc': return_county_ugc}}

os.makedirs(SAME_FOLDER_NAME, exist_ok=True)

for dataset_name, dataset_attributes in datasets.items():
    reader = shapefile.Reader(dataset_attributes['url'])
    collection = reader.shapeRecords()
    for region in collection.__geo_interface__['features']:
        write_to_file(region, dataset_attributes['namefunc'](region))
        # symlink coastal zones to a SAME code
        if dataset_name in {'coastal', 'offshore'}:
            for rows in lookup_data:
                # check the two-letter area code in the UGC against each row
                if region['properties']['ID'][:2] == rows['SSALPHA']:
                    symlink_same(return_marine_same(rows, region), return_simple_ugc(region))
        if dataset_name == 'county':
            symlink_same(return_county_same(region), return_county_ugc(region))