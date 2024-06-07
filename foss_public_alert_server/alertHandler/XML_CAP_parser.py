# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import requests

from .abstract_CAP_parser import AbstractCAPParser
import feedparser
from django.conf import settings


class XMLCAPParser(AbstractCAPParser):

    def __init__(self, source_id, feed_url):
        super().__init__(source_id, feed_url)
        self.parser = feedparser

    def get_feed(self):
        try:
            print("fetching: " + self.feed_url)
            feed = self.parser.parse(self.feed_url)

            #print("got: " + str(feed))

            for entry in feed['entries']:
                print("Found Entry")
                # print(entry)
                # find the link to the CAP source
                cap_source_url = ''
                for link in entry['links']:
                    if link['type'] == 'application/cap+xml':  # may also application/rss+xml
                        cap_source_url = link['href']
                if not cap_source_url and len(entry['links']) == 1:
                    cap_source_url = entry['links'][0]['href']
                if not cap_source_url:
                    continue

                # if we have expiry data available here already, check that
                # to avoid additional downloads
                try:
                    expire_time = datetime.datetime.fromisoformat(entry.get('cap_expires'))
                    if expire_time is not None and expire_time < datetime.datetime.now(datetime.timezone.utc):
                        print(f"{self.source} - not downloading alert {cap_source_url} expired on {expire_time}")
                        continue
                except ValueError as e:
                    print(f"Failed to parse expiry time: {entry.get('cap_expires')}")
                except TypeError as e:
                    pass

                try:
                    req = self.session.get(cap_source_url, headers={'User-Agent': settings.USER_AGENT}) #@todo load user agent from config
                    if not req.ok:
                        print(f"Fetch error {req.status_code}: {cap_source_url}")
                        continue
                except requests.exceptions.ConnectionError as e:
                    print(f"Connection error: {cap_source_url}")
                    continue

                cap_data = req.content.decode('utf-8')
                print("got feed, call addAlert")
                self.addAlert(cap_source_url=cap_source_url, cap_data=cap_data)

        except Exception as e:
            print("Something went wrong while getting the Feed: " + str(e))
            # @todo add to error logger

        print("got feed")
