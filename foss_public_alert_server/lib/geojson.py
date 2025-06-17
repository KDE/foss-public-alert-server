# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import pyclipper

from lib import geomath


def geojson_distance(p1, p2):
    """
    Returns the distance in meters between two GeoJSON coordinates
    """
    return geomath.distance(p1[1], p1[0], p2[1], p2[0])


def geojson_distance_to_line(l1, l2, p):
    """
    Distance in meters from p to a line given by coordinates l1 and l2.
    """
    line_length = pow(pow(l1[0] - l2[0], 2) + pow(l1[1] - l2[1], 2), 0.5)
    if line_length == 0:
        return geojson_distance(l1, p)

    d = (p[0] - l1[0]) * (l2[0] - l1[0]) + (p[1] - l1[1]) * (l2[1] - l1[1])
    r = max(0.0, min(1.0, d / (line_length * line_length)))
    i = [l1[0] + r * (l2[0] - l1[0]), l1[1] + r * (l2[1] - l1[1])]
    return geojson_distance(i, p)


def geojson_ring_douglas_peucker(ring, threshold):
    """
    Douglas-Peucker geometry simplification applied to a polygon
    ring in GeoJSON format with a threshold in meters.
    """
    if len(ring) < 3:
        return ring

    max_distance = 0.0
    max_dist_idx = 1
    for i in range(1, len(ring) - 1):
        d = geojson_distance_to_line(ring[0], ring[-1], ring[i])
        if (d > max_distance):
            max_distance = d
            max_dist_idx = i

    if max_distance > threshold:
        left = geojson_ring_douglas_peucker(ring[:max_dist_idx], threshold)
        right = geojson_ring_douglas_peucker(ring[max_dist_idx:], threshold)
        return left + right
    else:
        return [ring[0], ring[-1]]


def geojson_path_bounding_box(path, min_p=[180, 90], max_p=[-180, -90]):
    """
    A pair of coordinates with the minimum and maximum from a given GeoJSON path.
    """
    for p in path:
        min_p = [min(min_p[0], p[0]), min(min_p[1], p[1])]
        max_p = [max(max_p[0], p[0]), max(max_p[1], p[1])]
    return (min_p, max_p)


def geojson_multipolygon_bounding_box(multi_polygon):
    """
    Same as the above, but for an GeoJSON MultiPolygon.
    """
    min_p = [180, 90]
    max_p = [-180, -90]
    for poly in multi_polygon:
        min_p, max_p = geojson_path_bounding_box(poly[0], min_p, max_p)
    return (min_p, max_p)


def geojson_ring_simplify(ring, threshold):
    """
    Apply Douglas-Peucker polygon simplification with a given threshold in meters
    to a polygon ring, and ensure the result remains a valid polygon.
    """
    bbox = geojson_path_bounding_box(ring)
    ring_length = len(ring)
    ring = geojson_ring_douglas_peucker(ring, threshold)
    if len(ring) < 5:
        print("replacing polygon with bounding box")
        ring = [bbox[0], [bbox[1][0], bbox[0][1]], bbox[1], [bbox[0][0], bbox[1][1]], bbox[0]]
    else:
        print(f"polygon simplification dropped {ring_length - len(ring)} of {ring_length} points")
    return ring


def geojson_multipolygon_offset(multi_polygon, offset):
    """
    Apply polygon offset (specified in meters) to the given GeoJSON MultiPolyong.
    """
    # Clipper uses integer coordinates, so scale everything to the OSM-typcial 100 nano-degree
    CLIPPER_SCALE = 10000000

    bbox = geojson_multipolygon_bounding_box(multi_polygon)
    lat_center = (bbox[0][1] + bbox[1][1]) / 2.0
    bbox_width = geojson_distance([bbox[0][0], lat_center], [bbox[1][0], lat_center])
    bbox_height = geojson_distance(bbox[0], [bbox[0][1], bbox[0][1]])

    clipper_offset = ((bbox[1][0] - bbox[0][0]) / min(bbox_width, bbox_height)) * offset * CLIPPER_SCALE

    pc = pyclipper.PyclipperOffset()
    for poly in multi_polygon:
        pc.AddPath(pyclipper.scale_to_clipper(poly[0], CLIPPER_SCALE), pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
    poly_tree = pc.Execute2(clipper_offset)

    result = []
    for node in poly_tree.Childs:
        outer_ring = pyclipper.scale_from_clipper(node.Contour, CLIPPER_SCALE)
        outer_ring.append(outer_ring[0])  # Clipper doesn't return closed polygons, but GeoJSON expects those
        result.append([outer_ring])

    return result


def geojson_path_round_coordinates(path, decimals):
    """
    Round coordinates in the given GeoJSON path to a given maximum amount of decimals.
    """
    for coordinate in path:
        coordinate[0] = round(coordinate[0], decimals)
        coordinate[1] = round(coordinate[1], decimals)
    return path


def geojson_polygon_round_coordinates(polygon, decimals):
    """
    Round coordinates in the given GeoJSON Polygon to a given maximum amount of decimals.
    """
    for ring in polygon:
        ring = geojson_path_round_coordinates(ring, decimals)
    return polygon


def geojson_multipolygon_round_coordinates(multi_polygon, decimals):
    """
    Round coordinates in the given GeoJSON MultiPolygon to a given maximum amount of decimals.
    """
    for poly in multi_polygon:
        poly = geojson_polygon_round_coordinates(poly, decimals)
    return multi_polygon
