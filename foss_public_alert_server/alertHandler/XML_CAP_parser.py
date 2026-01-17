# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import warnings
import datetime
import requests
import logging
import feedparser
import os

from feedparser import FeedParserDict
from dateutil import parser

from django.http import HttpResponseNotModified
from django.conf import settings

from .exceptions import NothingChangedException
from .abstract_CAP_parser import AbstractCAPParser
from .models import Alert
from sourceFeedHandler.models import CAPFeedSource
from lib import cap_feed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CAP_MIMETYPES = ['application/common-alerting-protocol+xml', 'application/cap+xml']
BROKEN_CHAIN_FEEDS = ['sa-ncm-ar', 'sa-ncm-en', 'gh-gmet-en', 'za-saws-en']
BROKEN_CHAIN_FILE = os.path.join(settings.BASE_DIR, 'alertHandler/data/broken-chains.pem')

class XMLCAPParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "xml_parser")

    def _load_alerts_from_feed(self):
        logger.debug(f"fetching: {self.feed_source.source_id}")
        # use etags to reduce network load
        last_e_tag = self.feed_source.last_e_tag
        feed: FeedParserDict

        try:
            verify = True
            if self.feed_source.source_id in BROKEN_CHAIN_FEEDS:
                verify = BROKEN_CHAIN_FILE
            headers = {'User-Agent': settings.USER_AGENT}
            if last_e_tag is not None:
                headers['If-None-Match'] = last_e_tag
            feed_request = requests.get(self.feed_source.cap_alert_feed, verify=verify, headers=headers)
            feed: FeedParserDict = feedparser.parse(feed_request.content)

            # check if the feed contains any error and raise Exception if so
            if feed.bozo:
                raise feed.bozo_exception
        except feedparser.exceptions.CharacterEncodingOverride as e:
            # the feed does not follow the rules in RFC 3023 feedparser tried a different encoding
            # if the encoding can not be determined feedparser raised a CharacterEncodingUnknown exception
            warnings.warn(f"CharacterEncodingOverride error feed does not follow RFC 3023. Parse anyway. - {e}")
        except feedparser.NonXMLContentType as e:
            # the feed does not follow the rules in RFC 3023 and serve the feed in a wrong content type
            # feedparser tries to parse the feed anyway
            warnings.warn(f"NonXMLContentType - feed does not follow RFC 3023. Parse anyway. - {e}")

        if feed_request.status_code == 304:
            raise NothingChangedException("Nothing changed")

        # check if header has en etag and if yes update the etag in the database
        if "etag" in feed_request.headers:
            new_etag = feed_request.headers["etag"]
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_e_tag=new_etag)

        for entry in feed['entries']:
            # find the link to the CAP source
            cap_source_url = ''
            for link in entry['links']:
                if link['type'] in CAP_MIMETYPES:  # TODO: may also application/rss+xml
                    cap_source_url = link['href']
            if not cap_source_url and len(entry['links']) == 1:
                cap_source_url = entry['links'][0]['href']
            if not cap_source_url:
                continue

            # if we have expiry data available here already, check that
            # to avoid additional downloads
            expire_time = cap_feed.CAPFeedEntry.expiry_time(entry)
            if expire_time is not None and expire_time < datetime.datetime.now(datetime.timezone.utc):
                logger.debug(f"Alert Expired: {self.feed_source.source_id} - not downloading alert {cap_source_url} expired on {expire_time} - skipping")
                continue

            # if we have an identifier and sent time available here, check whether we
            # know the alert already
            try:
                cap_ident = entry.get('cap_identifier')
                cap_sent = entry.get('cap_sent')
                if cap_ident is not None and cap_sent is not None:
                    sent_time = parser.isoparse(cap_sent)
                if len(Alert.objects.filter(source_id=self.feed_source.source_id, alert_id=cap_ident, issue_time=sent_time)) == 1:
                    self.record_unchanged_alert(cap_ident)
                    continue
            except Exception:
                pass

            try:
                if self.feed_source.source_id in BROKEN_CHAIN_FEEDS:
                    # upgrade http to https as a workaround for za-saws-en
                    cap_source_url = cap_source_url.replace('http://', 'https://')
                    req = self.session.get(cap_source_url, headers={'User-Agent': settings.USER_AGENT}, verify=BROKEN_CHAIN_FILE)
                else:
                    req = self.session.get(cap_source_url, headers={'User-Agent': settings.USER_AGENT})
                if not req.ok:
                    logger.error(f"Fetch error {req.status_code}: {cap_source_url}")
                    continue
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {cap_source_url}")
                continue

            if req.from_cache and cap_ident:
                self.record_unchanged_alert(cap_ident)
                continue

            cap_data = req.content.decode('utf-8')
            # add alert to database
            self.addAlert(cap_source_url=cap_source_url, cap_data=cap_data)