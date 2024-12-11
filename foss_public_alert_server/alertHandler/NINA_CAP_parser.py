# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import re
import requests
import xml.etree.ElementTree as ET

from sourceFeedHandler.models import CAPFeedSource

from .abstract_CAP_parser import AbstractCAPParser

# Parser for BBK's CAP-like JSON API
# see https://nina.api.bund.dev/
#
# For MoWaS alerts this produces identical results than
# using the API implemented in MoWaSCapParser, but for
# LHP this lacks details.
class NinaCapParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "nina_parser")

    @staticmethod
    def convertProperty(xmlParent, mowasObj, propertyName):
        if not propertyName in mowasObj:
            return
        node = ET.SubElement(xmlParent, '{urn:oasis:names:tc:emergency:cap:1.2}' + propertyName)
        node.text = mowasObj[propertyName]

    @staticmethod
    def filterPolygon(polyData):
        # remove nonsense coordinates
        polyData = re.sub(r'-1.0,-1.0 ', '', polyData)
        # swap latitude/longitude pairs into the right order
        return re.sub(r'(-?\d+\.\d+),(-?\d+\.\d+)', r'\2,\1', polyData)

    def get_json(self, url):
        try:
            req = self.session.get(url)
            if not req.ok:
                print(f"Fetch error {req.status_code}: {url}")
                return None
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {url}")
            return None
        return req.json()

    def _load_alerts_from_feed(self):
        # use last e tag to reduce network usage
        # TODO fix cache handling and distinguish between empty result and no change for removing obsolete alerts
        headers = {
            "ETag": self.feed_source.last_e_tag, # what if None?
        }
        response = requests.get(self.feed_source.cap_alert_feed, headers=headers)  # @todo why not cached?
        if response.status_code == 304:
            # print(f"Nothing changed for {self.feed_source.source_id}")
            return
        elif response.status_code != 200:
            raise "Feed status code is not 200"

        # update etag and store it in the database
        new_etag = response.headers.get("ETag")
        # print(f"etag is {new_etag}")
        CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_e_tag=new_etag)

        feed_data = json.loads(response.content)
        print(feed_data)
        for alert_id_obj in feed_data:
            alert_id = alert_id_obj["id"]

            alert = self.get_json(f"https://warnung.bund.de/api31/warnings/{alert_id}.json")
            geojson = self.get_json(f"https://warnung.bund.de/api31/warnings/{alert_id}.geojson")
            if not alert or not geojson:
                continue

            print(alert)
            ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
            root = ET.Element('{urn:oasis:names:tc:emergency:cap:1.2}alert')

            for prop in ['identifier', 'sender', 'sent', 'status', 'msgType', 'scope', 'note', 'references']:
                self.convertProperty(root, alert, prop)

            for alert_info in alert['info']:
                info = ET.SubElement(root, '{urn:oasis:names:tc:emergency:cap:1.2}info',
                                     {'lang': alert_info['language']})
                for category in alert_info['category']:
                    cat = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}category')
                    cat.text = category

                for prop in ['event', 'urgency', 'severity', 'certainty', 'headline', 'description', 'instruction',
                             'expires', 'web', 'contact']:
                    self.convertProperty(info, alert_info, prop)

                for event_code in alert_info.get('eventCode', []):
                    event_code_node = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}eventCode')
                    for prop in ['valueName', 'value']:
                        self.convertProperty(event_code_node, event_code, prop)

                for param in alert_info.get('parameter', []):
                    param_node = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}parameter')
                    for prop in ['valueName', 'value']:
                        self.convertProperty(param_node, param, prop)
                    if param['valueName'] == 'sender_signature':
                        sender_name_node = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}senderName')
                        sender_name_node.text = param['value']

                for area in alert_info['area']:
                    area_node = ET.SubElement(info, '{urn:oasis:names:tc:emergency:cap:1.2}area')
                    self.convertProperty(area_node, area, 'areaDesc')
                    for poly in area.get('polygon', []):
                        poly_node = ET.SubElement(area_node, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
                        poly_node.text = self.filterPolygon(poly)
                    for code in area['geocode']:
                        code_node = ET.SubElement(area_node, '{urn:oasis:names:tc:emergency:cap:1.2}geocode')
                        for prop in ['valueName', 'value']:
                            self.convertProperty(code_node, code, prop)
                    # TODO more area content

            # merge area geometry
            print(geojson)
            geojson = geojson['features'][0] # TODO
            for area in root.findall('.//{urn:oasis:names:tc:emergency:cap:1.2}area'):
                for geocode in area.findall('{urn:oasis:names:tc:emergency:cap:1.2}geocode'):
                    code_name = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}valueName').text
                    code_value = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}value').text
                    if not code_name or not code_value:
                        continue
                    # append geojson to original file
                    if geojson['geometry']['type'] == 'Polygon':
                        poly = ET.SubElement(area, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
                        poly.text = self.geojson_polygon_to_cap(geojson['geometry']['coordinates'])
                        expanded = True
                    elif geojson['geometry']['type'] == 'MultiPolygon':
                        for coordinates in geojson['geometry']['coordinates']:
                            poly = ET.SubElement(area, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
                            poly.text = self.geojson_polygon_to_cap(coordinates)
                        expanded = True
                    else:
                        print(f"{self.feed_source.source_id} - unhandled geometry type: {geojson['geometry']['type']}")

            self.addAlert(cap_data=ET.tostring(root, encoding='utf-8', xml_declaration=True).decode())
