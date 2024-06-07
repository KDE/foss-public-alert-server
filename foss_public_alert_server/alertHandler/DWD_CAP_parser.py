# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import io
import requests
import zipfile

from .abstract_CAP_parser import AbstractCAPParser


class DWDCAPParser(AbstractCAPParser):

    def __init__(self, feed_url, source_id):
        super().__init__(feed_url, source_id)

    def get_feed(self):
        feed_data = requests.get(self.feed_url)
        zip_file = zipfile.ZipFile(io.BytesIO(feed_data.content), 'r')
        for cap_file in zip_file.namelist():
            cap_data = zip_file.read(cap_file).decode('utf-8')
            self.addAlert(cap_data = cap_data)
