# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from lib import cap, geomath


def cap_polygon_to_geojson(cap_polygon):
    poly = []
    for cap_coord in cap.CAPPolygon.parse_polygon(cap_polygon):
        poly.append([cap_coord[0], cap_coord[1]])
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


def cap_info_to_geojson(cap_info: cap.CAPAlertInfo):
    """
    Returns a GeoJSON feature object for an XML CAP alert info.
    """
    geometry = {}

    geometry['type'] = 'MultiPolygon'
    geometry['coordinates'] = []

    for poly in cap_info.polygons():
        geometry['coordinates'].append(cap_polygon_to_geojson(poly))
    for circle in cap_info.circles():
        geometry['coordinates'].append(cap_circle_to_geojson(circle))

    properties = {}
    properties['event'] = cap_info.event()
    properties['severity'] = cap_info.severity()
    properties['urgency'] = cap_info.urgency()

    feature = {}
    feature['type'] = 'Feature'
    feature['properties'] = properties
    feature['geometry'] = geometry

    return feature


def cap_alert_to_geojson(cap_msg: cap.CAPAlertMessage):
    """
    Returns a GeoJSON feature collection for the given CAP alert.
    """

    features = []
    for cap_info in cap_msg.alert_infos():
        feature = cap_info_to_geojson(cap_info)
        feature['properties']['msgType'] = cap_msg.msg_type()
        feature['properties']['status'] = cap_msg.status()
        features.append(feature)

    featureColl = {}
    featureColl['type'] = 'FeatureCollection'
    featureColl['name'] = cap_msg.identifier()
    featureColl['features'] = features
    return featureColl


cap_msg = cap.CAPAlertMessage.from_file(sys.argv[1])
geojson = cap_alert_to_geojson(cap_msg)
print(json.dumps(geojson))
