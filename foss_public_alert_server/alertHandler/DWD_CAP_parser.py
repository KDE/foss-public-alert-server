# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import io
import requests
import zipfile
import logging

from django.http import HttpResponseNotModified, HttpResponseBase

from .exceptions import NothingChangedException, FeedFetchException

logger = logging.getLogger("app")

from .abstract_CAP_parser import AbstractCAPParser
from sourceFeedHandler.models import CAPFeedSource


class DWDCAPParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "dwd_parser")

    def _load_alerts_from_feed(self):
        # use last e tag to reduce network usage
        headers = {
            "If-None-Match": self.feed_source.last_e_tag,  # what if None?
        }
        response = requests.get(self.feed_source.cap_alert_feed, headers=headers, timeout=10)  # @todo why not cached?
        if response.status_code == HttpResponseNotModified.status_code:
            raise NothingChangedException("Nothing changed")
        elif response.status_code != HttpResponseBase.status_code:
            raise FeedFetchException(f"Feed returned HTTP {HttpResponseBase.status_code}")

        # update etag and store it in the database
        new_etag = response.headers.get("ETag")
        CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_e_tag=new_etag)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content), 'r')
        for cap_file in zip_file.namelist():
            cap_data = zip_file.read(cap_file).decode('utf-8')
            self.addAlert(cap_data=cap_data)
