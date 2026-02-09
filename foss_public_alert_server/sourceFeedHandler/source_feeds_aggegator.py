# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests
import json
import os
import logging
from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

alert_hub_feeds_url = 'https://alert-hub-sources.s3.amazonaws.com/json'
fpas_feeds_file = os.path.join(settings.BASE_DIR, "sourceFeedHandler/custom_feeds.json")
aggregated_feed_object = {}


def get_alert_hub_feeds() -> json:
    """
    fetch the json feeds file from the aler thub
    :return: the json data with the feeds form the alert hub
    """
    response = requests.get(alert_hub_feeds_url)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        logger.error('Error while loading alerthub data')


def get_fpas_feeds() -> json:
    """
    open the custom FPAS Feeds file and return the json data
    :return: the custom feeds from FPAS
    """
    with open(fpas_feeds_file, 'r') as file:
        data = json.load(file)
    return data


def append_one_feed_to_json_list(data: json) -> None:
    """
    append the given data to the aggregated_feed_object sources list
    :param data: json data of one feed source
    :return: None
    """
    aggregated_feed_object["sources"].append(data)


def parse_one_alert_hub_feed(data: json) -> None:
    """
    appends some custom properties to the json data and append it to the list
    :param data: json data of one alert-hub feeds source
    :return: None
    """
    # add custom feature to the json
    data['source']['feedSource'] = "alert-hub"
    data['source']['format'] = "rss or atom"

    append_one_feed_to_json_list(data)


def parse_one_custom_feed(data: json):
    if data['source'].get('override', False):
        source_id: str = data['source']["sourceId"]
        # update all properties set in the override
        for entry in aggregated_feed_object["sources"]:
            if entry['source']['sourceId'] == source_id:
                entry['source'].update(data['source'])
                return

        logger.error(f"{source_id} marked as override but no such feed found!")
        return

    append_one_feed_to_json_list(data)


def parse_feeds_and_create_new_json() -> json:
    """
    parse all feed sources and merge all feeds in a new file
    :return: None
    """
    alert_hub_feeds: json = get_alert_hub_feeds()
    fpas_feeds: json = get_fpas_feeds()

    aggregated_feed_object["sources"] = []

    for i in alert_hub_feeds['sources']:
        parse_one_alert_hub_feed(i)

    for j in fpas_feeds['sources']:
        parse_one_custom_feed(j)

    return aggregated_feed_object
