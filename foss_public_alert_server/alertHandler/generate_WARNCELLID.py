# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: 2022 Volker Krause <vkrause@kde.org>
# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import requests

DATA_FOLDER = 'data/WARNCELLID'

# note: coastal WARNCELLIDs are symlinked from the EMMA_IDs dataset, check generate_EMMA_ID.py
LAKES_URL = 'https://maps.dwd.de/geoserver/dwd/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=dwd%3AWarngebiete_Binnenseen&outputFormat=application%2Fjson'

def write_to_file(geojson):
    path = os.path.join(os.path.dirname(__file__), DATA_FOLDER, str(geojson['properties']['WARNCELLID']) + ".geojson")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(geojson))
        f.close()

# autofetch from DWD's GeoServer instance
lakes = requests.get(LAKES_URL, timeout=10).json()

# load geojson data
for region in lakes['features']:
    write_to_file(region)
