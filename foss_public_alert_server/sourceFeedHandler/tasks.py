# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from .models import CAPFeedSource
import json
from celery import shared_task

from alertHandler import abstract_CAP_parser
from alertHandler.XML_CAP_parser import XMLCAPParser
from alertHandler.MOWAS_CAP_parser import MoWaSCapParser
from alertHandler.DWD_CAP_parser import DWDCAPParser
from . import source_feeds_aggegator

def store_feeds_in_database(feeds: json):
    for feed in feeds["sources"]:
        # only store the feeds in the database that are not ignored by us
        if not feed["source"]["ignore"]:
            new_feed = CAPFeedSource(
                source_id=feed["source"]["sourceId"],
                code=feed["source"]["byLanguage"][0]["code"],
                name=feed["source"]["byLanguage"][0]["name"],
                logo=feed["source"]["byLanguage"][0]["logo"],
                guid = feed["source"].get("guid"),
                #guid=  feed["source"]["guid"] if feed["source"]["guid"] is not None else None,
                #register_url=feed["source"]["registerUrl"],
                register_url = feed["source"].get("registerUrl"),
                source_is_official=feed["source"]["sourceIsOfficial"],
                cap_alert_feed=feed["source"]["capAlertFeed"],
                cap_alert_feed_status=feed["source"]["capAlertFeedStatus"],
                authorityCountry=feed["source"]["authorityCountry"],
                authorityAbbrev=feed["source"]["authorityAbbrev"],
                feedSource=feed["source"]["feedSource"],
                format=feed["source"]["format"],
                ignore=feed["source"]["ignore"]
            )
            new_feed.save()

@shared_task(name="task.reload_feed_sources_and_update_database")
def reload_feed_sources_and_update_database() -> None:
    """
    called from the periodic celery task to update the feed sources json and update the database
    :return: None
    """
    # load new feeds and recreated json file
    feeds = source_feeds_aggegator.parse_feeds_and_create_new_json()
    # @todo validate json file before replacing the old database
    # clear old entries and store new feed in database
    CAPFeedSource.objects.all().delete()
    store_feeds_in_database(feeds)


@shared_task(name="task.create_parser_and_get_feed")
def create_parser_and_get_feed(feed_id: str, feed_format:str) -> None :
    """
    called from the periodic celery task. Creates a parser instance and get the feed
    :param feed_id: the id of the CAPFeedSource entry
    :param feed_format: the format field of the CAPFeedSource entry
    :return: None
    """
    print("Current feed id: " + feed_id)
    feed = CAPFeedSource.objects.get(id=feed_id)
    parser: abstract_CAP_parser = None
    # create parser corresponding to the feed format
    match feed_format:
        case "rss or atom":
            # print("its atom")
            parser = XMLCAPParser(feed)
        case "de-mowas":
            # print("its mowas")
            parser = MoWaSCapParser(feed)
        case "DWD-Zip":
            # print("its dwd")
            parser = DWDCAPParser(feed)
    if parser is not None:
        parser.get_feed(parser)
    else:
        print(f"{feed.source_id}: Parser is None for {feed_format}")


# for manually update the feed sources in the database
# reload_feed_sources_and_update_database()
