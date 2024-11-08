# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import io
import requests
import zipfile

from .abstract_CAP_parser import AbstractCAPParser
from sourceFeedHandler.models import CAPFeedSource


class DWDCAPParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "dwd_parser")

    def _load_alerts_from_feed(self):
        # use last e tag to reduce network usage
        headers = {
        "ETag": self.feed_source.last_e_tag,  # what if None?
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

        zip_file = zipfile.ZipFile(io.BytesIO(response.content), 'r')
        for cap_file in zip_file.namelist():
            cap_data = zip_file.read(cap_file).decode('utf-8')
            self.addAlert(cap_data=cap_data)
