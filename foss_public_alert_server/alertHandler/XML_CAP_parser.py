# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import requests

import feedparser
from feedparser import FeedParserDict

from django.conf import settings

from .abstract_CAP_parser import AbstractCAPParser
from sourceFeedHandler.models import CAPFeedSource


class XMLCAPParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "xml_parser")
        self.parser = feedparser

    def _load_alerts_from_feed(self):
        print("fetching: " + self.feed_source.source_id)
        # use etags to reduce network load
        last_e_tag = self.feed_source.last_e_tag
        # the etag can be none, so only use it, if it is not none
        if last_e_tag is not None:
            feed: FeedParserDict = self.parser.parse(self.feed_source.cap_alert_feed, etag=last_e_tag) # @todo change user agent
        else:
            feed: FeedParserDict = self.parser.parse(self.feed_source.cap_alert_feed)

        if feed.status == 304:
            # print(f"Nothing changed for {self.feed_source.source_id}")
            return
        elif feed.status != 200:
            raise "Feed status code is not 200"

        # check if header has en etag and if yes update the etag in the database
        if "etag" in feed.headers:
            new_etag = feed.headers["etag"]
            # print(f"etag is {new_etag}")
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_e_tag=new_etag)
        else:
            # print("feed does not have an etag")
            pass

        # print("got: " + str(feed))

        for entry in feed['entries']:
            # print("Found Entry")
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
                    print(f"Alert Expired: {self.feed_source.source_id} - not downloading alert {cap_source_url} expired on {expire_time} - skipping")
                    continue
            except ValueError as e:
                print(f"Failed to parse expiry time: {entry.get('cap_expires')}")
            except TypeError as e:
                pass

            try:
                req = self.session.get(cap_source_url, headers={'User-Agent': settings.USER_AGENT})
                if not req.ok:
                    print(f"Fetch error {req.status_code}: {cap_source_url}")
                    continue
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {cap_source_url}")
                continue

            cap_data = req.content.decode('utf-8')
            # print("got feed, call addAlert")
            # add alert to database
            self.addAlert(cap_source_url=cap_source_url, cap_data=cap_data)
