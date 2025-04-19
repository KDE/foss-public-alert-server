# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import shapefile

# note: CURRENT_DATE may need to be updated from time to time in the case of new releases with a later valid date.
CURRENT_DATE = '18mr25'
FOLDER_NAME = 'data/UGC/'

COASTAL_LINK = f'https://www.weather.gov/source/gis/Shapefiles/WSOM/mz{CURRENT_DATE}.zip'  # check https://www.weather.gov/gis/MarineZones for updates
OFFSHORE_LINK = f'https://www.weather.gov/source/gis/Shapefiles/WSOM/oz{CURRENT_DATE}.zip' # check https://www.weather.gov/gis/MarineZones for updates
ZONES_LINK = f'https://www.weather.gov/source/gis/Shapefiles/WSOM/z_{CURRENT_DATE}.zip'    # check https://www.weather.gov/gis/PublicZones for updates
COUNTY_LINK = f'https://www.weather.gov/source/gis/Shapefiles/County/c_{CURRENT_DATE}.zip' # check https://www.weather.gov/gis/Counties for updates

def write_to_file(geojson, name):
    path = os.path.join(os.path.dirname(__file__), FOLDER_NAME, name + '.geojson')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(geojson))
        f.close()

# dummy function to return complete UGC from coastal and offshore datasets
def return_simple_id(polygon):
    return polygon['properties']['ID']

# assembles UGC in ssZnnn format, where ss is the state code and zzz is the zone number
def return_zone_ugc(polygon):
    return f'{polygon['properties']['STATE']}Z{polygon['properties']['ZONE']}'

# assembles UGC in ssCnnn format, where ss is the state code and nnn is the FIPS number.
# the [2:] is to strip out the state number.
def return_county_ugc(polygon):
    return f'{polygon['properties']['STATE']}C{polygon['properties']['FIPS'][2:]}'

datasets = {'coastal': {'url': COASTAL_LINK, 'namefunc': return_simple_id},
            'offshore': {'url': OFFSHORE_LINK, 'namefunc': return_simple_id},
            'zones': {'url': ZONES_LINK, 'namefunc': return_zone_ugc},
            'county': {'url': COUNTY_LINK, 'namefunc': return_county_ugc}}

for dataset_name, dataset_attributes in datasets.items():
    reader = shapefile.Reader(dataset_attributes['url'])
    collection = reader.shapeRecords()
    for region in collection.__geo_interface__['features']:
        write_to_file(region, dataset_attributes['namefunc'](region))
