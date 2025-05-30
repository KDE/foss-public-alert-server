# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import xml.etree.ElementTree as ET
import datetime
from zoneinfo import ZoneInfo


class AlertSwiss:
    """
    AlertSwiss JSON to CAP converter
    """

    @staticmethod
    def add_property(xmlParent, capPropertyName: str, value):
        """
        internal
        """
        node = ET.SubElement(xmlParent, '{urn:oasis:names:tc:emergency:cap:1.2}' + capPropertyName)
        node.text = value

    @staticmethod
    def json_to_cap_info(alert, language):
        """
        Create a CAP info element based on the given alert JSON object.
        """
        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')

        info = ET.Element('{urn:oasis:names:tc:emergency:cap:1.2}info')
        AlertSwiss.add_property(info, 'language', language)
        if 'publisherName' in alert:
            AlertSwiss.add_property(info, 'senderName', alert['publisherName'])
        AlertSwiss.add_property(info, 'headline', alert['title']['title'])
        if alert['description']['description']:
            AlertSwiss.add_property(info, 'description', alert['description']['description'])
        for inst in alert['instructions']:
            AlertSwiss.add_property(info, 'instruction', inst['text'])  # TODO image links?
        for link in alert['links']:
            AlertSwiss.add_property(info, 'web', link['href'])
        if alert['contact']['contact']:
            AlertSwiss.add_property(info, 'contact', alert['contact']['contact'])
        AlertSwiss.add_property(info, 'event', alert['event'])
        if alert['allClear']:
            AlertSwiss.add_property(info, 'responseType', 'AllClear')

        serverity_map = {
            'minor': 'Minor',
            'moderate': 'Moderate'
            # TODO which other values are there?
        }
        AlertSwiss.add_property(info, 'severity', serverity_map.get(alert['severity'], 'Unknown'))
        AlertSwiss.add_property(info, 'urgency', 'Unknown')

        # TODO nationWide - do we need to add geometry for this?
        for area in alert['areas']:
            capArea = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}area')
            AlertSwiss.add_property(capArea, 'areaDesc', area['description']['description'])
            for polygon in area['polygons']:
                capCoords = [','.join(x) for x in polygon['coordinates']]
                AlertSwiss.add_property(capArea, 'polygon', ' '.join(capCoords))
            # TODO circles, regions

        # TODO images

        return info

    @staticmethod
    def json_to_cap_message(alert):
        """
        Convert a single alert JSON object into a corresponding CAP alert root object.
        Note: this does not add CAP info elements, this needs to be done separately
        in order to merge multiple languages.
        """
        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
        root = ET.Element('{urn:oasis:names:tc:emergency:cap:1.2}alert')
        AlertSwiss.add_property(root, 'identifier', alert['identifier'])
        dtStart = alert['sent'].index(' ') + 1  # strip off localized weekday
        sentDt = datetime.datetime.strptime(alert['sent'][dtStart:], '%d.%m.%Y, %H:%M')
        sentDt = sentDt.replace(tzinfo=ZoneInfo('Europe/Zurich'))
        AlertSwiss.add_property(root, 'sent', sentDt.isoformat())
        AlertSwiss.add_property(root, 'sender', alert['sender'])
        AlertSwiss.add_property(root, 'references', alert['reference'])
        AlertSwiss.add_property(root, 'scope', 'Public')
        AlertSwiss.add_property(root, 'msgType', 'Alert')
        if alert['testAlert']:
            AlertSwiss.add_property(root, 'status', 'Exercise')
        elif alert['technicalTestAlert']:
            AlertSwiss.add_property(root, 'status', 'Test')
        else:
            AlertSwiss.add_property(root, 'status', 'Actual')

        return root
