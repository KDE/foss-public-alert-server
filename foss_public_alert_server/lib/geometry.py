# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from . import geomath

from django.contrib.gis.geos import MultiPolygon, Polygon


def polygon_from_cap_polygon(cap_polygon):
    """
    Create a PostGis Polygon from a CAP polygon description.
    """
    coords = []
    for cap_coord in cap_polygon.split(' '):
        cap_point = cap_coord.split(',')
        if len(cap_point) != 2:
            continue
        try:
            coord = (float(cap_point[1]), float(cap_point[0]))
        except Exception:
            continue
        coords.append(coord)

    if len(coords) < 4:
        return None
    # ensure polygon is closed
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    return Polygon(coords)


def polygon_from_cap_circle(cap_circle):
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
    return Polygon(poly)


def multipolygon_from_cap_info(cap_info):
    polys = []
    for poly_node in cap_info.findall('{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}polygon'):
        polys.append(polygon_from_cap_polygon(poly_node.text))
    for circle_node in cap_info.findall('{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}circle'):
        polys.append(polygon_from_cap_circle(circle_node.text))

    return MultiPolygon(polys)
