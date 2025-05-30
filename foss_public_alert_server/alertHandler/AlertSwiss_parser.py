# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import requests
import xml.etree.ElementTree as ET
import logging

from django.http import HttpResponseBase

from .abstract_CAP_parser import AbstractCAPParser

from lib.alertswiss import AlertSwiss

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSwissParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "alertswiss_parser")

    languages = ["de", "fr", "it", "en"]

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
        alerts = {}

        # this neither supports If-Modified-Since nor If-None-Match (etags)...
        for lang in self.languages:
            response = requests.get(self.feed_source.cap_alert_feed.replace("{LANG}", lang))
            if response.status_code != HttpResponseBase.status_code:
                raise "Feed status code is not 200"

            feed_data = json.loads(response.content)
            for alert in feed_data["alerts"]:
                ident = alert["identifier"]
                if ident not in alerts:
                    alerts[ident] = {}
                alerts[ident][lang] = alert

        for ident, alert in alerts.items():
            cap_msg = None
            for lang, info in alert.items():
                if not cap_msg:
                    cap_msg = AlertSwiss.json_to_cap_message(info)
                cap_msg.append(AlertSwiss.json_to_cap_info(info, lang))
            self.addAlert(cap_data=ET.tostring(cap_msg, encoding='utf-8', xml_declaration=True).decode())
