from .models import CAPFeedSource
import json

rewrite_feed_source = True

feeds_file = "aggregated_feeds.json"


def get_feeds() -> json:
    """
    open the custom FPAS Feeds file and return the json data
    :return: the custom feeds from FPAS
    """
    with open(feeds_file, 'r') as file:
        data = json.load(file)
    return data


def store_feeds_in_database():
    feeds = get_feeds()

    for feed in feeds["sources"]:
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



if rewrite_feed_source:
    CAPFeedSource.objects.all().delete()
    store_feeds_in_database()