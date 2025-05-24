# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests
import logging
import xml.etree.ElementTree as ET

from dateutil import parser

from django.http import HttpResponseNotModified
from django.conf import settings

from .exceptions import NothingChangedException
from .abstract_CAP_parser import AbstractCAPParser
from sourceFeedHandler.models import CAPFeedSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# make the CAP namespace the default one
ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')

class EDXLCAPParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "edxl_parser")

    def _load_alerts_from_feed(self):
        logger.info(f"fetching: {self.feed_source.source_id}")
        # use etags to reduce network load
        last_e_tag = self.feed_source.last_e_tag
        response: requests.Response
        feed: ET.Element
        
        if last_e_tag is not None:
            response: requests.Response = requests.get(self.feed_source.cap_alert_feed, headers={'If-None-Match': last_e_tag, 'User-Agent': settings.USER_AGENT})
        else:
            response: requests.Response = requests.get(self.feed_source.cap_alert_feed)
        
        if response.status_code == HttpResponseNotModified.status_code:
            raise NothingChangedException("Nothing changed")

        # check if header has en etag and if yes update the etag in the database
        if "etag" in response.headers:
            new_etag = response.headers["etag"]
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_e_tag=new_etag)

        feed: ET.Element = ET.fromstring(response.text)
        for entry in feed.findall('{urn:oasis:names:tc:emergency:EDXL:DE:1.0}contentObject'):
            alert_xml = entry.find('{urn:oasis:names:tc:emergency:EDXL:DE:1.0}xmlContent')[0][0]
            cap_data = ET.tostring(alert_xml, 'unicode')
            # add alert to database
            self.addAlert(cap_data=cap_data)