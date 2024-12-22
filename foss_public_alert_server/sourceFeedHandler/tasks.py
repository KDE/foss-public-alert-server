# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from .models import CAPFeedSource
import json
from celery import shared_task

from alertHandler import abstract_CAP_parser
from alertHandler.XML_CAP_parser import XMLCAPParser
from alertHandler.MOWAS_CAP_parser import MoWaSCapParser
from alertHandler.NINA_CAP_parser import NinaCapParser
from alertHandler.DWD_CAP_parser import DWDCAPParser
from . import source_feeds_aggegator

def compare(compare_description, old_entry, new_entry) -> bool:
    """
    Compare two values and return True if there are different,
    False if they have the same value
    """
    if old_entry != new_entry and old_entry is not None:
        # something changed
        print(f"{compare_description} changed - {old_entry} is now {new_entry}")
        return True
    else:
        return False

def store_feeds_in_database(feeds: json):
    current_entries = CAPFeedSource.objects.all()
    new_feed_ids = {feed["source"]["sourceId"] for feed in feeds["sources"]}
    # delete all feed which are not in the new feed list
    for entry in current_entries:
        if entry.source_id not in new_feed_ids:
            print(f"Delete old feed: {entry.source_id}")
            current_entries.delete()

    for feed in feeds["sources"]:
        # only store the feeds in the database that are not ignored by us
        if not feed["source"]["ignore"]:
            add_feed = False
            if current_entries.filter(source_id=feed["source"]["sourceId"]).exists():
                current_entry: CAPFeedSource = current_entries.get(source_id=feed["source"]["sourceId"])
                # check if there are changes
                something_changed = False
                something_changed |= compare("code", current_entry.code, feed["source"]["byLanguage"][0]["code"])
                something_changed |= compare("name", current_entry.name, feed["source"]["byLanguage"][0]["name"])
                something_changed |= compare("logo", current_entry.logo, feed["source"]["byLanguage"][0]["logo"])
                something_changed |= compare("guid", current_entry.guid, feed["source"].get("guid", ""))
                something_changed |= compare("register_url", current_entry.register_url, feed["source"].get("registerUrl"))
                something_changed |= compare("source_is_official", current_entry.source_is_official, feed["source"]["sourceIsOfficial"])
                something_changed |= compare("cap_alert_feed", current_entry.cap_alert_feed, feed["source"]["capAlertFeed"])
                something_changed |= compare("cap_alert_feed_status", current_entry.cap_alert_feed_status, feed["source"]["capAlertFeedStatus"])
                something_changed |= compare("authorityCountry", current_entry.authorityCountry, feed["source"]["authorityCountry"])
                something_changed |= compare("authorityAbbrev", current_entry.authorityAbbrev, feed["source"]["authorityAbbrev"])
                something_changed |= compare("feedSource", current_entry.feedSource, feed["source"]["feedSource"])
                something_changed |= compare("format", current_entry.format, feed["source"]["format"])
                something_changed |= compare("ignore", current_entry.ignore, feed["source"]["ignore"])

                if something_changed:
                    # delete the changed entry and set flag to re-add the feed
                    current_entry.delete()
                    add_feed = True
                else:
                    # Nothing changed for the feed, we don't have to modify it
                    print(f"Nothing changed for the feed {feed["source"]["sourceId"]}, skipping...")
                    continue
            else:
                # we don't have an entry of this feed
                print(f"Feed {feed["source"]["sourceId"]} does not exists in our database, adding...")
                add_feed = True

            if add_feed:
                print(f"add new feed: {feed["source"]["sourceId"]}")
                new_feed = CAPFeedSource(
                    source_id=feed["source"]["sourceId"],
                    code=feed["source"]["byLanguage"][0]["code"],
                    name=feed["source"]["byLanguage"][0]["name"],
                    logo=feed["source"]["byLanguage"][0]["logo"],
                    guid = feed["source"].get("guid"),
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
        case "de-nina":
            parser = NinaCapParser(feed)
        case "DWD-Zip":
            # print("its dwd")
            parser = DWDCAPParser(feed)
    if parser is not None:
        parser.get_feed(parser)
    else:
        print(f"{feed.source_id}: Parser is None for {feed_format}")


# for manually update the feed sources in the database
# reload_feed_sources_and_update_database()
