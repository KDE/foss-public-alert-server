# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os

# download the geojson from MeteoAlarm's Google Drive (linked at https://meteoalarm.org/en/live/page/redistribution-hub#list)
file_name_geojson = "data/EMMA_ID/geocodes.json"
folder_name = "data/EMMA_ID/"

def write_to_file(geojson):
    print(geojson)
    path = os.path.join(os.path.dirname(__file__), folder_name, geojson['properties']['code'] + ".geojson")
    with open(path, 'w') as f:
        f.write(json.dumps(geojson))

geojson = json.loads(open(file_name_geojson, 'r').read())
for region in geojson['features']:
    write_to_file(region)
