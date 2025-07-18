# SPDX-FileCopyrightText: 2025 Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
import json
import pathlib


parser = argparse.ArgumentParser(description='Merge content from all given GeoJSON files containing a sinlge Feature into a single GeoJSON FeatureCollection')
parser.add_argument('input', type=str, help='Input GeoGJSON files', nargs='+')
arguments = parser.parse_args()

featureCollection = {}
featureCollection['type'] = 'FeatureCollection'
featureCollection['features'] = []
for fn in arguments.input:
    if pathlib.Path(fn).is_symlink():
        continue
    with open(fn) as f:
        feature = json.load(f)
        featureCollection['features'].append(feature)

print(json.dumps(featureCollection))
