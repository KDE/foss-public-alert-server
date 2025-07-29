# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
notes: this script does not have auto-fetch capability.
Download the geocodes from https://github.com/GaryBikini/ChinaAdminDivisonSHP/tree/master
use https://github.com/solidjerryc/chinese-coordinate-converter to convert them into WGS84
and export the new layer as a GeoJSON file.
The script expects the source files at the path data/CPEAS Geographic Code/[country, province, city, district].geojson
They will self-destruct to save space - make sure to keep a copy somewhere else!
"""

import json
import os

FOLDER_NAME = "data/CPEAS Geographic Code"

def write_to_file(geojson, name):
    path = os.path.join(os.path.dirname(__file__), FOLDER_NAME, name + '.geojson')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(geojson))
        f.close()

# this defines all the datasets with the link, name attribute and folder
datasets = {
    'country': {'filename': 'country.geojson', 'name': 'cn_adcode'},
    'province': {'filename': 'province.geojson', 'name': 'pr_adcode'},
    'city': {'filename': 'city.geojson', 'name': 'ct_adcode'},
    'district': {'filename': 'district.geojson', 'name': 'dt_adcode'}
}
os.makedirs(FOLDER_NAME, exist_ok=True)
for dataset_name, dataset_attributes in datasets.items():
    source_file_path = os.path.join(FOLDER_NAME, dataset_attributes['filename'])
    with open(source_file_path, 'r', encoding='utf-8') as dataset_file:
        collection = json.loads(dataset_file.read())
        for region in collection['features']:
            write_to_file(region, f'{region['properties'][dataset_attributes['name']]}000000')
        dataset_file.close()
    os.remove(source_file_path)
