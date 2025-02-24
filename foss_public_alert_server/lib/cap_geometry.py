# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from . import cap, geomath

from django.contrib.gis.geos import MultiPolygon, Polygon


def polygon_from_cap_polygon(cap_polygon):
    """
    Create a GEOS Polygon from a CAP polygon description.
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
    """
    Create a GEOS Polygon from a CAP circle description.
    """
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


def multipolygon_from_cap_alert(cap_alert: cap.CAPAlertMessage):
    """
    Returns a GEOS MultiPolygon for the affected area of the given CAP alert message.
    """
    polys = []
    for cap_poly in cap_alert.polygons():
        polys.append(polygon_from_cap_polygon(cap_poly))
    for cap_circle in cap_alert.circles():
        polys.append(polygon_from_cap_circle(cap_circle))

    return MultiPolygon(polys)
