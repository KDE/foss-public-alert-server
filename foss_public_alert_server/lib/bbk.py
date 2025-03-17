# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import re
import xml.etree.ElementTree as ET

from lib import cap_geojson


class BBK:
    """
    Utilities for consuming JSON data from Germany's BBK
    """

    @staticmethod
    def convertProperty(xmlParent, mowasObj, propertyName):
        if propertyName not in mowasObj:
            return
        node = ET.SubElement(xmlParent, '{urn:oasis:names:tc:emergency:cap:1.2}' + propertyName)
        node.text = mowasObj[propertyName]

    @staticmethod
    def filterPolygon(polyData):
        # remove nonsense coordinates
        polyData = re.sub(r'-1.0,-1.0 ', '', polyData)
        # swap latitude/longitude pairs into the right order
        return re.sub(r'(-?\d+\.\d+),(-?\d+\.\d+)', r'\2,\1', polyData)

    @staticmethod
    def json_to_cap(alert):
        """
        Convert the given CAP alert in BBK's JSON format to a CAP XML tree.
        """
        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
        root = ET.Element('{urn:oasis:names:tc:emergency:cap:1.2}alert')

        for prop in ['identifier', 'sender', 'sent', 'status', 'msgType', 'scope', 'note', 'references']:
            BBK.convertProperty(root, alert, prop)

        for alert_info in alert['info']:
            info = ET.SubElement(root, '{urn:oasis:names:tc:emergency:cap:1.2}info', {'lang': alert_info['language']})
            for category in alert_info['category']:
                cat = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}category')
                cat.text = category

            for prop in ['event', 'urgency', 'severity', 'certainty', 'headline', 'description', 'instruction', 'expires', 'web', 'contact']:
                BBK.convertProperty(info, alert_info, prop)

            for event_code in alert_info.get('eventCode', []):
                event_code_node = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}eventCode')
                for prop in ['valueName', 'value']:
                    BBK.convertProperty(event_code_node, event_code, prop)

            for param in alert_info.get('parameter', []):
                param_node = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}parameter')
                for prop in ['valueName', 'value']:
                    BBK.convertProperty(param_node, param, prop)
                if param['valueName'] == 'sender_signature':
                    sender_name_node = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}senderName')
                    sender_name_node.text = param['value']

            for area in alert_info['area']:
                area_node = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}area')
                BBK.convertProperty(area_node, area, 'areaDesc')
                for poly in area.get('polygon', []):
                    poly_node = ET.SubElement(area_node, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
                    poly_node.text = BBK.filterPolygon(poly)
                for code in area.get('geocode', []):
                    code_node = ET.SubElement(area_node, '{urn:oasis:names:tc:emergency:cap:1.2}geocode')
                    for prop in ['valueName', 'value']:
                        BBK.convertProperty(code_node, code, prop)
                # TODO more area content

        return root

    @staticmethod
    def resolve_area_geometry(alert, geojson):
        """
        Merge GeoJSON affected area information into a CAP structure
        converted from BBK CAP-like JSON.
        """
        for area in alert.findall('.//{urn:oasis:names:tc:emergency:cap:1.2}area'):
            for geocode in area.findall('{urn:oasis:names:tc:emergency:cap:1.2}geocode'):
                code_name = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}valueName').text
                code_value = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}value').text
                if code_name != 'AreaId' or not code_value:
                    continue
                geo = cap_geojson.geojson_find_features(geojson, 'areaId', int(code_value))
                cap_geojson.geojson_features_to_cap(area, geo)
