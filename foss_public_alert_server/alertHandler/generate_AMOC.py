# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import ftplib
import shapefile

FOLDER_NAME = "data/AMOC-AreaCode"

def write_to_file(geojson):
    path = os.path.join(os.path.dirname(__file__), FOLDER_NAME, geojson['properties']['AAC'] + '.geojson')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(geojson))
        f.close()

datasets = ['IDM00001', 'IDM00003', 'IDM00007', 'IDM00014', 'IDM00017', 'IDM00020']

f = ftplib.FTP('ftp.bom.gov.au')
f.login()
f.cwd('anon/home/adfd/spatial')
os.makedirs(FOLDER_NAME, exist_ok=True)

for dataset in datasets:
    with open(os.path.join(FOLDER_NAME, f'{dataset}.zip'), 'wb') as file:
        f.retrbinary(f'RETR {dataset}.zip', file.write)
        print(f'{dataset} downloaded, now processing')
        file.close()
    reader = shapefile.Reader(os.path.join(FOLDER_NAME, f'{dataset}.zip'))
    collection = reader.shapeRecords()
    for region in collection.__geo_interface__['features']:
        write_to_file(region)
    os.remove(os.path.join(FOLDER_NAME, f'{dataset}.zip'))
    print(f'{dataset} processed')