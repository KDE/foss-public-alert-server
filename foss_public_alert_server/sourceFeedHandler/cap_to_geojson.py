# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import xml.etree.ElementTree as ET

from lib import geomath
from lib import polygon_simplifier


def cap_polygon_to_geojson(cap_polygon):
    poly = []
    for cap_coord in cap_polygon.split(' '):
        cap_point = cap_coord.split(',')
        if len(cap_point) != 2:
            continue
        try:
            coord = [float(cap_point[1]), float(cap_point[0])]
        except Exception:
            continue
        poly.append(coord)
    return [poly]


def cap_circle_to_geojson(cap_circle):
    (center, radius) = cap_circle.split(' ')
    (lat, lon) = center.split(',')
    try:
        lat = float(lat)
        lon = float(lon)
        radius = float(radius) * 1000.0  # CAP specifies radius in kilometer, we need meter below
    except Exception:
        return []

    dlon = radius / geomath.distance(lat, 0.0, lat, 1.0)
    dlat = radius / geomath.distance(0.0, lon, 1.0, lon)
    poly = [
        [lon - dlon, lat - dlat],
        [lon - dlon, lat + dlat],
        [lon + dlon, lat + dlat],
        [lon + dlon, lat - dlat],
        [lon - dlon, lat - dlat],
    ]
    return [poly]


def cap_to_geojson(cap_file):
    """
    Returns a GeoJSON feature object for an XML CAP alert in cap_file
    """

    ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
    cap_root = ET.parse(cap_file).getroot()

    # TODO consider all other info elements as well
    cap_info = cap_root.find('{urn:oasis:names:tc:emergency:cap:1.2}info')

    geometry = {}
    geometry['type'] = 'MultiPolygon'
    geometry['coordinates'] = []

    for poly_node in cap_info.findall('{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}polygon'):
        geometry['coordinates'].append(cap_polygon_to_geojson(poly_node.text))
    for circle_node in cap_info.findall('{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}circle'):
        geometry['coordinates'].append(cap_circle_to_geojson(circle_node.text))

    properties = {}
    properties['msgType'] = cap_root.find('{urn:oasis:names:tc:emergency:cap:1.2}msgType').text
    properties['status'] = cap_root.find('{urn:oasis:names:tc:emergency:cap:1.2}status').text
    properties['event'] = cap_info.find('{urn:oasis:names:tc:emergency:cap:1.2}event').text
    properties['severity'] = cap_info.find('{urn:oasis:names:tc:emergency:cap:1.2}severity').text
    properties['urgency'] = cap_info.find('{urn:oasis:names:tc:emergency:cap:1.2}urgency').text
    properties['category'] = cap_info.find('{urn:oasis:names:tc:emergency:cap:1.2}category').text

    feature = {}
    feature['type'] = 'Feature'
    feature['properties'] = properties
    feature['geometry'] = polygon_simplifier.simplify_geometry(geometry, 2000.0, 2)
    return feature
