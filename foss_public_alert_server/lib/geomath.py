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
