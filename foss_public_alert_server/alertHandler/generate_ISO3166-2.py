# SPDX-FileCopyrightText: 2023 Volker Krause <vkrause@kde.org>
# SPDX-FileCopyrightText: 2024 Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os.path
import requests
import zipfile
import math
import pyclipper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_name = "data/ISO3166-2/iso3166-2-boundaries.zip"
folder_name = "data/ISO3166-2/"
file_name_geojson = "data/ISO3166-2/iso3166-2-boundaries.geojson"

threshold = 10000  # Path simplification threshold (in meter)
decimals = 13  # Number of decimals in coordinate output

ISO3166_2_VERSION = '2021-08-16'
ISO3166_2_URL = f"https://volkerkrause.eu/~vkrause/iso3166-boundaries/iso3166-2-boundaries.geojson-{ISO3166_2_VERSION}.zip"


def download_iso3166File():
    name = os.path.join(os.path.dirname(__file__), file_name)
    zip_location = os.path.join(os.path.dirname(__file__), folder_name)
    if os.path.exists(name):
        return
    logger.info(f"Downloading {ISO3166_2_URL}...")
    r = requests.get(ISO3166_2_URL)
    if r.status_code < 400:
        with open(name, 'wb') as f:
            f.write(r.content)
        with zipfile.ZipFile(name, 'r') as z:
            z.extractall(path=zip_location)


def lineLength(p1, p2):
    return pow(pow(p1[0] - p2[0], 2) + pow(p1[1] - p2[1], 2), 0.5)


# distance in meters between two geographic coordinates
def distance(p1, p2):
    earthRadius = 6371000.0
    d_lat = math.radians(p1[1] - p2[1])
    d_lon = math.radians(p1[0] - p2[0])
    a = pow(math.sin(d_lat / 2.0), 2) + math.cos(math.radians(p1[1])) * math.cos(math.radians(p2[1])) * pow(
        math.sin(d_lon / 2.0), 2)
    return 2.0 * earthRadius * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


# distance in meters from p to a line given by coordinates l1 and l2
def distanceToLine(l1, l2, p):
    line_length = lineLength(l1, l2)
    if line_length == 0:
        return distance(l1, p)

    d = (p[0] - l1[0]) * (l2[0] - l1[0]) + (p[1] - l1[1]) * (l2[1] - l1[1])
    r = max(0.0, min(1.0, d / (line_length * line_length)))
    i = [l1[0] + r * (l2[0] - l1[0]), l1[1] + r * (l2[1] - l1[1])]
    return distance(i, p)


# min/max coordinates of a sequence of coordinates
def boundingBox(ring):
    minP = [180, 90]
    maxP = [-180, -90]
    for p in ring:
        minP = [min(minP[0], p[0]), min(minP[1], p[1])]
        maxP = [max(maxP[0], p[0]), max(maxP[1], p[1])]
    return [minP, maxP]


# Polygon simplification
def douglasPeucker(ring, threshold):
    if len(ring) < 3:
        return ring

    maxDistance = 0.0
    maxDistIdx = 1
    for i in range(1, len(ring) - 1):
        d = distanceToLine(ring[0], ring[-1], ring[i])
        if (d > maxDistance):
            maxDistance = d
            maxDistIdx = i

    if maxDistance > threshold:
        left = douglasPeucker(ring[:maxDistIdx], threshold)
        right = douglasPeucker(ring[maxDistIdx:], threshold)
        return left + right
    else:
        return [ring[0], ring[-1]]


# Finding and simplifying boundary polygons specificially for Transport API
def simplifyRing(ring):
    bbox = boundingBox(ring)

    # deal with tiny enclaves/exclaves like Baarle "in" BE/NL
    if distance(bbox[0], bbox[1]) < threshold:
        logger.info("dropping polygon with bounding box below threshold")
        return []

    ring_length = len(ring)
    ring = douglasPeucker(ring, threshold)
    if len(ring) < 5:
        logger.info("polygon degenerated, using bounding box instead")
        ring = [bbox[0], [bbox[1][0], bbox[0][1]], bbox[1], [bbox[0][0], bbox[1][1]], bbox[0]]
    else:
        logger.info(f"polygon simplification dropped {ring_length - len(ring)} of {ring_length} points")
    return ring


# Apply polygon offset (specified in meters) to the given ring
def offsetRing(ring, offset):
    # Clipper uses integer coordinates, so scale everything to the OSM-typcial 100 nano-degree
    CLIPPER_SCALE = 10000000

    bbox = boundingBox(ring)
    latCenter = (bbox[0][1] + bbox[1][1]) / 2.0
    bboxWidth = distance([bbox[0][0], latCenter], [bbox[1][0], latCenter])
    clipperOffset = ((bbox[1][0] - bbox[0][0]) / bboxWidth) * offset * CLIPPER_SCALE

    pc = pyclipper.PyclipperOffset()
    pc.AddPath(pyclipper.scale_to_clipper(ring, CLIPPER_SCALE), pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
    result = pyclipper.scale_from_clipper(pc.Execute(clipperOffset), CLIPPER_SCALE)[0]
    if len(result) > 0:
        result.append(result[0])  # Clipper doesn't return closed polygons, but GeoJSON expects those
    return result


# Round coordinates in the given ring
def roundCoordinates(ring, decimals):
    for coordinate in ring:
        coordinate[0] = round(coordinate[0], decimals)
        coordinate[1] = round(coordinate[1], decimals)
    return ring


# Simplify a polygon, using the following approach:
# - Apply the Douglas-Peucker algorithm to remove points within arguments.threshold
# - Offset the outer ring by arguments.threshold to ensure we still cover the original polygon completely
# - Offset all inner rings by -arugments.threshold for the same reason
def simplifyMultiPolygon(multiPoly):
    for i in range(0, len(multiPoly)):
        # outer ring
        multiPoly[i][0] = simplifyRing(multiPoly[i][0])
        if not multiPoly[i][0]:
            multiPoly[i] = None
            continue
        multiPoly[i][0] = offsetRing(multiPoly[i][0], threshold)
        # inner rings
        for j in range(1, len(multiPoly[i])):
            multiPoly[i][j] = simplifyRing(multiPoly[i][j])
            offsetRing(multiPoly[i][0], -threshold)
        multiPoly[i] = [roundCoordinates(ring, decimals) for ring in multiPoly[i] if ring]
    multiPoly = [poly for poly in multiPoly if poly]
    return multiPoly


def write_to_file(geojson):
    print(geojson)
    path = os.path.join(os.path.dirname(__file__), folder_name, geojson['properties']['ISO3166-2'] + ".geojson")
    with open(path, 'w') as f:
        f.write(json.dumps(geojson))


# download data if necessary
download_iso3166File()

# load geojson
geojson = json.loads(open(file_name_geojson, 'r').read())
for region in geojson['features']:
    if region['geometry']['type'] == 'MultiPolygon':
        region['geometry']['coordinates'] = simplifyMultiPolygon(region['geometry']['coordinates'])
    else:
        region['geometry']['coordinates'] = simplifyMultiPolygon([region['geometry']['coordinates']])

    write_to_file(region)
