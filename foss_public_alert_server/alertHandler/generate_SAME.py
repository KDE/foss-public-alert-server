# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os

# download the shapefile from https://www.weather.gov/gis/NWRPartialCounties (data in public domain)
# extract the geojson e.g. with QGIS - Desktop and run this script to separate each code
# in the future we should find a solution to extract the geojson in python directly
file_name_geojson = "data/SAME/codes.geojson"
folder_name = "data/SAME/"

def write_to_file(geojson):
    print(geojson)
    path = os.path.join(os.path.dirname(__file__), folder_name, geojson['properties']['AREA_SAME'] + ".geojson")
    with open(path, 'w') as f:
        f.write(json.dumps(geojson))

geojson = json.loads(open(file_name_geojson, 'r').read())
for region in geojson['features']:
    write_to_file(region)
