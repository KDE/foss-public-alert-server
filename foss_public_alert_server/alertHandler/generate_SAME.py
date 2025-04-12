# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import shapefile

date = "18mr25" 
shapefile_url = f"https://www.weather.gov/source/gis/Shapefiles/County/cs{date}.zip"
folder_name = "data/SAME/"

def write_to_file(geojson):
    path = os.path.join(os.path.dirname(__file__), folder_name, geojson['properties']['AREA_SAME'] + ".geojson")
    with open(path, 'w') as f:
        f.write(json.dumps(geojson))
        f.close()

reader = shapefile.Reader(shapefile_url)
collection = reader.shapeRecords()
for region in collection.__geo_interface__['features']:
    write_to_file(region)
