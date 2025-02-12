# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import math


def distance(lat1, lon1, lat2, lon2):
    """
    Computes the distance in meters between two geographic coordinates.
    """
    earth_radius = 6371000.0  # in meters
    d_lat = math.radians(lat1 - lat2)
    d_lon = math.radians(lon1 - lon2)
    a = math.pow(math.sin(d_lat / 2.0), 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.pow(math.sin(d_lon / 2.0), 2)
    return 2.0 * earth_radius * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def distance_to_point(p1, p2):
    """
    Computes the distance in meters between two geographic coordinates.

    :param p1,p1 Coordinates as GeoJson point
    """
    return distance(p1[1], p1[0], p2[1], p2[0])


def distance_to_line(l1, l2, p):
    """
    Distance in meters from p to a line given by coordinates l1 and l2
    """

    line_length = pow(pow(l1[0] - l2[0], 2) + pow(l1[1] - l2[1], 2), 0.5)
    if line_length == 0:
        return distance_to_point(l1, p)

    d = (p[0] - l1[0]) * (l2[0] - l1[0]) + (p[1] - l1[1]) * (l2[1] - l1[1])
    r = max(0.0, min(1.0, d / (line_length * line_length)))
    i = [l1[0] + r * (l2[0] - l1[0]), l1[1] + r * (l2[1] - l1[1])]
    return distance_to_point(i, p)
