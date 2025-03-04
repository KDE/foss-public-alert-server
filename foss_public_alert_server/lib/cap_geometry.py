# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from lib import cap
from lib import geomath

from django.contrib.gis.geos import MultiPolygon, Polygon


def polygon_from_cap_polygon(cap_polygon):
    """
    Create a GEOS Polygon from a CAP polygon description.
    """
    coords = cap.CAPPolygon.parse_polygon(cap_polygon)

    poly = Polygon(coords)
    if not poly.valid:
        poly = poly.make_valid()  # try to fix self-intersections

    return poly


def polygon_from_cap_circle(cap_circle: str):
    """
    Create a list of GEOS Polygons from a CAP circle description.
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

    # if the circle would cross the antimeridian, cut it into two parts
    if lon - dlon >= -180 and lon + dlon <= 180:
        return [Polygon.from_bbox((lon - dlon, lat - dlat, lon + dlon, lat + dlat))]

    if lon - dlon < -180:
        return [Polygon.from_bbox((lon - dlon + 360, lat - dlat, 180, lat + dlat)),
                Polygon.from_bbox((-180, lat - dlat, lon + dlon, lat + dlat))]
    if lon + dlon > 180:
        return [Polygon.from_bbox((lon - dlon, lat - dlat, 180, lat + dlat)),
                Polygon.from_bbox((-180, lat - dlat, lon + dlon - 360, lat + dlat))]


def multipolygon_from_cap_alert(cap_alert: cap.CAPAlertMessage):
    """
    Returns a GEOS MultiPolygon for the affected area of the given CAP alert message.
    """
    polys = []
    for cap_poly in cap_alert.polygons():
        polys.append(polygon_from_cap_polygon(cap_poly))
    for cap_circle in cap_alert.circles():
        polys += polygon_from_cap_circle(cap_circle)
    polys = [p for p in polys if p is not None]

    # don't use MultiPolygon(polys), that assumes intersection-free
    # polygons. Instead do the more expensive-unioning that handles
    # overlapping polygons correctly.
    mp = MultiPolygon()
    for poly in polys:
        mp = mp.union(poly)

    # normalize to a MultiPolygon, if the above simplified the geometry,
    # we need that for storing this in the same DB column type
    return mp if mp.geom_typeid == 6 else MultiPolygon(mp)
