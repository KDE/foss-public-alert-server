# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import xml.etree.ElementTree as ET
from django.contrib.gis.geos import Polygon

def build_alert(alert_model):
    """
    Build the CAP XML tree for the given alert
    :param alert_model: the alert to build the XML tree from
    :return: String representation of the CAP Alert in XML
    """
    xml_tree = ET.Element("{urn:oasis:names:tc:emergency:cap:1.2}alert")

    alert_elements = {
        "identifier": alert_model.alert_id,
        "sender": alert_model.sender,
        "sent": alert_model.sent.isoformat(),
        "status": alert_model.status,
        "msgType": alert_model.msg_type,
        "scope": alert_model.scope
    }

    for element in alert_elements:
        if element is not None:
            node = ET.SubElement(xml_tree, '{urn:oasis:names:tc:emergency:cap:1.2}' + element)
            node.text = alert_elements[element]

    xml_tree.append(build_info(alert_model))

    return ET.tostring(xml_tree, encoding='utf-8', method='xml', xml_declaration=True)


def build_info(alert_model) -> ET.Element:
    """
    Build the XML "info" subtree of a CAP alert
    :param alert_model: the alert to build the XML tree from
    :return: the CAP Info xml tree
    """
    info_tree = ET.Element("{urn:oasis:names:tc:emergency:cap:1.2}info")

    info_elements = {'category': alert_model.category,
                     "event": alert_model.event,
                     'urgency': alert_model.urgency,
                     'severity': alert_model.severity,
                     'certainty': alert_model.certainty,
                     'senderName': "FOSS Public Alert Server",
                     'onset': alert_model.onset.isoformat(),
                     'expires': alert_model.expires.isoformat(),
                     'headline': alert_model.headline,
                     'description': alert_model.description,
                     'instruction': "There is no real danger. No action is required. This is just a test alert.",
                     }

    for element in info_elements:
        if element is not None:
            node = ET.SubElement(info_tree, '{urn:oasis:names:tc:emergency:cap:1.2}'+element)
            node.text = info_elements[element]

    info_tree.append(build_area(alert_model))

    return info_tree

def polygon_to_CAP_data(polygon:Polygon) -> str:
    """
    transform polygon into CAP format
    :param polygon: the polygon to transform
    :return: polygon as list of coordinates
    """
    coords = polygon.coords
    poly: str = ''

    for cord in coords[0][0]:
        poly += f"{cord[1]},{cord[0]} "

    return poly.strip()


def build_area(alert_model)-> ET.Element:
    """
    build the "area" XML subtree for a CAP alert
    :param alert_model: the alert to build the XML tree from
    :return: xml subtree for an area
    """
    area_tree = ET.Element("{urn:oasis:names:tc:emergency:cap:1.2}area")
    node = ET.SubElement(area_tree, '{urn:oasis:names:tc:emergency:cap:1.2}areaDesc')
    node.text = alert_model.areaDesc

    if alert_model.polygon is not None:
        node = ET.SubElement(area_tree, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
        node.text = polygon_to_CAP_data(alert_model.polygon)

    return area_tree