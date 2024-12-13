# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import re
import requests
import xml.etree.ElementTree as ET

from sourceFeedHandler.models import CAPFeedSource

from .abstract_CAP_parser import AbstractCAPParser
from .bbk import BBK

# Parser for BBK's CAP-like JSON API
# see https://nina.api.bund.dev/
#
# For MoWaS alerts this produces identical results than
# using the API implemented in MoWaSCapParser, but for
# LHP this lacks details.
class NinaCapParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "nina_parser")

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

    @staticmethod
    def geojson_find_feature(geojson, key, value):
        """
        Fine a feature in a GeoJSON feature set containing the specified property.
        :param geojson: A GeoJSON feature set
        :param key: Feature proeprty name
        :param value: Feature property value
        """
        for feature in geojson["features"]:
            if key in feature and feature[key] == value:
                return feature
        return None

    def _load_alerts_from_feed(self):
        # use last e tag to reduce network usage
        # TODO fix cache handling and distinguish between empty result and no change for removing obsolete alerts
        headers = {
            "ETag": self.feed_source.last_e_tag, # what if None?
        }
        response = requests.get(self.feed_source.cap_alert_feed, headers=headers)  # @todo why not cached?
        if response.status_code == 304:
            return
        elif response.status_code != 200:
            raise "Feed status code is not 200"

        # update etag and store it in the database
        new_etag = response.headers.get("ETag")
        # print(f"etag is {new_etag}")
        CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_e_tag=new_etag)

        feed_data = json.loads(response.content)
        for alert_id_obj in feed_data:
            alert_id = alert_id_obj["id"]

            alert = self.get_json(f"https://warnung.bund.de/api31/warnings/{alert_id}.json")
            geojson = self.get_json(f"https://warnung.bund.de/api31/warnings/{alert_id}.geojson")
            if not alert or not geojson:
                continue

            root = BBK.json_to_cap(alert)

            # merge area geometry
            for area in root.findall('.//{urn:oasis:names:tc:emergency:cap:1.2}area'):
                for geocode in area.findall('{urn:oasis:names:tc:emergency:cap:1.2}geocode'):
                    code_name = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}valueName').text
                    code_value = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}value').text
                    if code_name != 'AreaId' or not code_value:
                        continue
                    geo = NinaCapParser.geojson_find_feature(geojson, 'id', code_value)
                    self.geojson_feature_to_cap(area, geo)

            self.addAlert(cap_data=ET.tostring(root, encoding='utf-8', xml_declaration=True).decode())
