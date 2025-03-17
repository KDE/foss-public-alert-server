# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import requests
import xml.etree.ElementTree as ET
import logging

from django.http import HttpResponseNotModified, HttpResponseBase

from .exceptions import NothingChangedException

from lib.bbk import BBK

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    def get_json(self, url):
        try:
            req = self.session.get(url)
            if not req.ok:
                logger.error(f"Fetch error {req.status_code}: {url}")
                return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {url}",exc_info=True)
            return None
        return req.json()

    def _load_alerts_from_feed(self):
        # use last e tag to reduce network usage
        # TODO fix cache handling and distinguish between empty result and no change for removing obsolete alerts
        headers = {
            "ETag": self.feed_source.last_e_tag, # what if None?
        }
        response = requests.get(self.feed_source.cap_alert_feed, headers=headers)  # @todo why not cached?
        if response.status_code == HttpResponseNotModified.status_code:
            raise NothingChangedException("Nothing changed")
        elif response.status_code != HttpResponseBase.status_code:
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
            BBK.resolve_area_geometry(root, geojson)

            self.addAlert(cap_data=ET.tostring(root, encoding='utf-8', xml_declaration=True).decode())
