# SPDX-FileCopyrightText: 2023 Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import argparse
import json
import math
import os
import pathlib
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from lib import geojson


parser = argparse.ArgumentParser(description='Simplify GeoJSON polygons for use in CAP alerts.')
parser.add_argument('input', type=str, help='Input GeoGJSON file to simplify', nargs='+')
parser.add_argument('--expand', type=float, help='Ratio of the overall size to expand the polygon by', default=0.005)
parser.add_argument('--threshold', type=float, help='Ratio of the overall size to use as Douglas-Peucker simplification threshold', default=0.0025)
parser.add_argument('--shrink', type=float, help='Ratio of the overall size to shrink the polygon by', default=0.004)
arguments = parser.parse_args()


def simplify_multi_polygon(multi_poly):
    """
    Simplify a GeoJSON multi-polygon, using the following approach:
    - Drop inner rings (not supported by CAP)
    - Offset the outer ring by 0.5%. This makes narrow concave parts disappear (such as bays, fjords, etc)
      and it ensures that we still cover the original area despite the following step.
    - Apply the Douglas-Peucker algorithm to remove points within a 0.25% threshold.
    - Offset the result by -0.4%. This is to get back closer to the original coverage area.
    - Round GEOJSON coordinates to avoid floating point number serialization bloat.
    """

    # drop inner rings
    # CAP doesn't support polygons with cutouts, so drop those here
    for poly in multi_poly:
        del poly[1:]

    # determine the size of the covered area
    # we use that to adjust all parameters for the following relative to the size
    # of the covered area, ie. larger areas will be simplified with more aggressive parameters.
    bbox = geojson.geojson_multipolygon_bounding_box(multi_poly)
    lat_center = (bbox[0][1] + bbox[1][1]) / 2.0
    bbox_width = round(geojson.geojson_distance([bbox[0][0], lat_center], [bbox[1][0], lat_center]), 0)
    bbox_height = round(geojson.geojson_distance(bbox[0], [bbox[0][0], bbox[1][1]]), 0)
    dist = round(max(bbox_width, bbox_height))
    print(f"Area size: {bbox_width} x {bbox_height}m")

    if arguments.expand < arguments.shrink:
        print("WARNING: shrinking more than expanding, result will likely not include the original area!")
    offset1 = dist * arguments.expand
    threshold = offset1 * arguments.threshold
    offset2 = dist * arguments.shrink

    # use enough decimals to fit 1/10th of the simplification threshold
    coord_per_meter_lon = (bbox[1][0] - bbox[0][0]) / bbox_width
    coord_per_meter_lat = (bbox[1][1] - bbox[0][1]) / bbox_height
    decimals = int(-math.log(min(coord_per_meter_lat, coord_per_meter_lon) * threshold * 0.1, 10)) + 1

    print(f"Applying offset: {offset1}m…")
    r = geojson.geojson_multipolygon_offset(multi_poly, offset1)
    print(f"Applying Douglas-Peucker simplification with threshold {threshold}m…")
    for ring in r:
        ring[0] = geojson.geojson_ring_simplify(ring[0], threshold)
    print(f"Applying negative offset: {offset2}m…")
    r = geojson.geojson_multipolygon_offset(r, -offset2)
    print(f"Rounding to {decimals} decimals…")
    r = geojson.geojson_multipolygon_round_coordinates(r, decimals)
    return r


# apply simplification to all given GeoJSON files
for fn in arguments.input:
    if pathlib.Path(fn).is_symlink():
        continue
    with open(fn, 'r') as f:
        print(f"Simplifying {fn}…")
        g = json.load(f)

    if g['geometry']['type'] == 'MultiPolygon':
        g['geometry']['coordinates'] = simplify_multi_polygon(g['geometry']['coordinates'])
    elif g['geometry']['type'] == 'Polygon':
        g['geometry']['coordinates'] = simplify_multi_polygon([g['geometry']['coordinates']])[0]

    with open(fn, 'w') as f:
        json.dump(g, f)
