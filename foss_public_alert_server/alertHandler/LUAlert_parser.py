# SPDX-FileCopyrightText: 2025 applecuckoo <nufjoysb@duck.com>
# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import requests

from .abstract_CAP_parser import AbstractCAPParser
from .models import Alert


class LUAlertParser(AbstractCAPParser):
    def __init__(self, feed_source):
        super().__init__(feed_source, "lualert_parser")

    def _load_alerts_from_feed(self):
        filenames = []

        response: dict = requests.get(self.feed_source.cap_alert_feed).json()
        for alerts in response:
            try:
                cap_ident = alerts['identifier']
                sent_time = datetime.datetime.utcfromtimestamp(alerts['sent'] / 1000)
                if len(Alert.objects.filter(source_id=self.feed_source.source_id, alert_id=cap_ident, issue_time=sent_time)) == 1:
                    self.record_unchanged_alert(cap_ident)
                    continue
            except Exception:
                pass

            filenames.append(f"dump-alert.{alerts['identifier'].split('.')[1]}.xml")

        metadata: dict = requests.get("https://data.public.lu/api/1/datasets/alertes-du-systeme-lu-alert/").json()
        for resource in metadata["resources"]:
            if resource["title"] in filenames:
                alert = requests.get(resource["url"])
                self.addAlert(cap_source_url=resource["url"], cap_data=alert.content.decode('utf-8').replace('xmlns="urn:oasis:names:tc:emergency:cap:1.2:profile:cap-lu:1.0"', 'xmlns="urn:oasis:names:tc:emergency:cap:1.2"'))
