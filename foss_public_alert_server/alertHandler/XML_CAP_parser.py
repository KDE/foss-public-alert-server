# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import warnings
import datetime
import requests
import logging
import feedparser

from feedparser import FeedParserDict
from dateutil import parser

from django.http import HttpResponseNotModified
from django.conf import settings

from .Exceptions import NothingChangedException
from .abstract_CAP_parser import AbstractCAPParser
from sourceFeedHandler.models import CAPFeedSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XMLCAPParser(AbstractCAPParser):

    def __init__(self, feed_source):
        super().__init__(feed_source, "xml_parser")

    def _load_alerts_from_feed(self):
        logger.info(f"fetching: {self.feed_source.source_id}")
        # use etags to reduce network load
        last_e_tag = self.feed_source.last_e_tag
        feed: FeedParserDict

        try:
            # the etag can be none, so only use it, if it is not none
            if last_e_tag is not None:
                feed: FeedParserDict = feedparser.parse(self.feed_source.cap_alert_feed, etag=last_e_tag,
                                                         agent=settings.USER_AGENT)
            else:
                feed: FeedParserDict = feedparser.parse(self.feed_source.cap_alert_feed)

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

        if feed.status == HttpResponseNotModified.status_code:
            raise NothingChangedException("Nothing changed")

        # check if header has en etag and if yes update the etag in the database
        if "etag" in feed.headers:
            new_etag = feed.headers["etag"]
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_e_tag=new_etag)

        for entry in feed['entries']:
            # find the link to the CAP source
            cap_source_url = ''
            for link in entry['links']:
                if link['type'] == 'application/cap+xml':  # TODO: may also application/rss+xml
                    cap_source_url = link['href']
            if not cap_source_url and len(entry['links']) == 1:
                cap_source_url = entry['links'][0]['href']
            if not cap_source_url:
                continue

            # if we have expiry data available here already, check that
            # to avoid additional downloads
            try:
                if entry.get('cap_expires') is not None:
                    expire_time = parser.isoparse(entry.get('cap_expires'))
                    if expire_time is not None and expire_time < datetime.datetime.now(datetime.timezone.utc):
                        logger.info(f"Alert Expired: {self.feed_source.source_id} - not downloading alert "
                                    f"{cap_source_url} expired on {expire_time} - skipping")
                        continue
            except ValueError as e:
                logger.exception(f"Failed to parse expiry time: {entry.get('cap_expires')}", exc_info=e)
            except TypeError as e:
                logger.exception("Type error", exc_info=e)

            try:
                req = self.session.get(cap_source_url, headers={'User-Agent': settings.USER_AGENT})
                if not req.ok:
                    logger.error(f"Fetch error {req.status_code}: {cap_source_url}")
                    continue
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {cap_source_url}")
                continue

            cap_data = req.content.decode('utf-8')
            # add alert to database
            self.addAlert(cap_source_url=cap_source_url, cap_data=cap_data)
