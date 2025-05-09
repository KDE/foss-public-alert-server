# SPDX-FileCopyrightText: 2025 Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: 2022 Volker Krause <vkrause@kde.org>
# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import csv
import gdown

# note: these are Google Drive IDs, but they will always point to the latest revision of the file.
aliases_id = "1haP3_PFz9nYrEgLjCd_YvaCuMb9_5QC1"
geocodes_id = "16s24hYHfYQhKMNcP1hpgQmg13Yb8j0hV"

geocodes_filename = "data/EMMA_ID/geocodes.json"
aliases_filename = "data/EMMA_ID/geocodes-aliases.csv"
emma_folder = "data/EMMA_ID/"
data_folder = "data/"

include_aliases = [ 'FIPS', 'NUTS2', 'NUTS3', 'WARNCELLID' ]
# only include coastal datasets, as DWD already includes polygons for alerts over land.
include_warncellid_prefixes = [ '5' ]

def write_to_file(geojson):
    path = os.path.join(os.path.dirname(__file__), emma_folder, geojson['properties']['code'] + ".geojson")
    with open(path, 'w') as f:
        f.write(json.dumps(geojson))
        f.close()

# autofetch
gdown.download(id=geocodes_id, output=geocodes_filename)
gdown.download(id=aliases_id, output=aliases_filename)

# load geojson data
geojson = json.loads(open(geocodes_filename, 'r').read())
for region in geojson['features']:
    write_to_file(region)

# create symlinks
with open(aliases_filename, newline='') as f:
    geocodesAliases = list(csv.reader(f, delimiter=',', quotechar='"'))[1:]
for alias in geocodesAliases:
    if alias[2] not in include_aliases:
        continue
    # check prefix for WARNCELLIDs
    if alias[2] == 'WARNCELLID' and alias[1][:len(alias[1])-8] not in include_warncellid_prefixes:
        continue
    destDir = os.path.join(data_folder, alias[2])
    os.makedirs(os.path.join(destDir), exist_ok=True)
    dest = os.path.join(destDir, f"{alias[1]}.geojson")

    if os.path.isfile(dest):
        os.remove(dest)

    srcDir = os.path.join(data_folder, 'EMMA_ID')
    src = os.path.join(os.path.relpath(srcDir, destDir), f"{alias[0]}.geojson")
    os.symlink(src, dest)

# clean up source files
os.remove(geocodes_filename)
os.remove(aliases_filename)
