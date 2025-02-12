# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from . import geomath


def douglas_peucker(ring, threshold):
    """
    Dougles Peucker polygon simplification.

    :param ring a GeoJson-like ring (simple, closed polygon)
    :param threshold simplification threshold in meters
    """

    if len(ring) < 3:
        return ring

    max_dist = 0.0
    max_dist_idx = 1
    for i in range(1, len(ring) - 1):
        d = geomath.distance_to_line(ring[0], ring[-1], ring[i])
        if (d > max_dist):
            max_dist = d
            max_dist_idx = i

    if max_dist > threshold:
        left = douglas_peucker(ring[:max_dist_idx], threshold)
        right = douglas_peucker(ring[max_dist_idx:], threshold)
        return left + right
    else:
        return [ring[0], ring[-1]]


def bounding_box_for_ring(ring):
    """
    Returns the bounding box for a given GeoJSON ring, as pair of GeoJSON
    points.
    """
    minP = [180, 90]
    maxP = [-180, -90]
    for p in ring:
        minP = [min(minP[0], p[0]), min(minP[1], p[1])]
        maxP = [max(maxP[0], p[0]), max(maxP[1], p[1])]
    return [minP, maxP]


def simplify_ring(ring, threshold):
    """
    Apply Dougles Peucker polygon simplification to the given GeoJSON ring.

    :param theshold Simplification threshold in meters.
    """
    bbox = bounding_box_for_ring(ring)

    # feature is smaller than threshold, replace by bounding box
    if geomath.distance_to_point(bbox[0], bbox[1]) < threshold and len(ring) > 5:
        ring = [bbox[0], [bbox[1][0], bbox[0][1]], bbox[1], [bbox[0][0], bbox[1][1]], bbox[0]]
        return ring

    ring = douglas_peucker(ring, threshold)
    # polygon degenerated during simplification, replace by bounding box
    if len(ring) < 5:
        ring = [bbox[0], [bbox[1][0], bbox[0][1]], bbox[1], [bbox[0][0], bbox[1][1]], bbox[0]]
    return ring


def round_coordinates(ring, decimals):
    """
    Round coordinates in the given GeoJSON ring to a given number of decimals
    """
    for coordinate in ring:
        coordinate[0] = round(coordinate[0], decimals)
        coordinate[1] = round(coordinate[1], decimals)
    return ring


def simplify_geometry(geometry, threshold, decimals):
    """
    Simplify the given GeoJSON geometry.
    Can be either a MultiPolygon or a Polygon, all other geometry types aren't modified.

    :param threshold Polygon simplification threshold in meters.
    :param decimals Number of decimals the coordinates are rounded to. # TODO can we determine this automatically?
    """
    coords = geometry['coordinates']
    if geometry['type'] == 'MultiPolygon':
        for i in range(0, len(coords)):
            # outer ring
            coords[i][0] = simplify_ring(coords[i][0], threshold)
            if not coords[i][0]:
                coords[i] = None
            continue
            # inner rings
            for j in range(1, len(coords[i])):
                coords[i][j] = simplify_ring(coords[i][j])
            coords[i] = [round_coordinates(ring, decimals) for ring in coords[i] if ring]
        coords = [poly for poly in coords if poly]
        if len(coords) == 1:
            coords = coords[0]
            geometry['type'] = 'Polygon'
        geometry['coordinates'] = coords
    return geometry
