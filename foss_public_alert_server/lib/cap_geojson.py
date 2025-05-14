# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def geojson_polygon_to_cap(coordinates) -> str:
    """
    Converts a polygon to cap data
    :param coordinates:
    :return: a string with the coordinates
    """
    if len(coordinates[0]) < 4:
        return None
    poly: str = ''
    for coord in coordinates[0]:
        poly += f"{coord[1]:.4f},{coord[0]:.4f} "
    return poly.strip()


def geojson_find_features(geojson, key, value):
    """
    Fine all features in a GeoJSON feature set containing the specified property.
    :param geojson: A GeoJSON feature set
    :param key: Feature proeprty name
    :param value: Feature property value
    """
    result = []
    for feature in geojson["features"]:
        if key in feature["properties"] and feature["properties"][key] == value:
            result.append(feature)
    return result


def geojson_add_polygon_cap_element(area, geojson_poly):
    """
    Internal. Add a given polygon as CAP element to area.
    """
    cap_poly = geojson_polygon_to_cap(geojson_poly)
    if not cap_poly:
        logger.warning(f"discarding too small polygon: {geojson_poly}")
        return
    poly = ET.SubElement(area, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
    poly.text = cap_poly


def geojson_feature_to_cap(area, geojson) -> bool:
    """
    Add a GeoJSON polygon from a GeoJSON feature to the CAP <area> element.
    :param area: the CAP <area> element to add the geometry to
    :param geojson: A GeoJSON feature object
    :return: True if a viable polygon was found and could be added, False otherwise
    """
    if geojson['geometry']['type'] == 'Polygon':
        geojson_add_polygon_cap_element(area, geojson['geometry']['coordinates'])
        return True
    elif geojson['geometry']['type'] == 'MultiPolygon':
        for coordinates in geojson['geometry']['coordinates']:
            geojson_add_polygon_cap_element(area, coordinates)
        return True
    else:
        logger.warning(f"unhandled geometry type: {geojson['geometry']['type']}")
        return False


def geojson_features_to_cap(cap_area, geojson_features):
    """
    Same as the above, but for multiple GeoJSON features.
    """
    for geojson_feature in geojson_features:
        geojson_feature_to_cap(cap_area, geojson_feature)

