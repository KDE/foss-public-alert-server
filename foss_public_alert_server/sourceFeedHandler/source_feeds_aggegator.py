import requests
import json

alert_hub_feeds_url = 'https://alert-hub-sources.s3.amazonaws.com/json'
fpas_feeds_file = "custom_feeds.json"
aggregated_feed_file_name = "../aggregated_feeds.json"
aggregated_feed_object = {}
version_code = "0.0.1"
reload_feed_source: bool = False


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
        print('Error while loading alerthub data')


def get_fpas_feeds() -> json:
    """
    open the custom FPAS Feeds file and return the json data
    :return: the custom feeds from FPAS
    """
    with open(fpas_feeds_file, 'r') as file:
        data = json.load(file)
    return data


def write_json_file() -> None:
    """
    creates a new file for the json data and dump the aggregated_feed_object in it
    :return: None
    """
    with open(aggregated_feed_file_name, 'w') as file:
        # dump json object into file
        json.dump(aggregated_feed_object, file)


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
    data['source']['ignore'] = False

    append_one_feed_to_json_list(data)


def check_if_we_have_an_override(authority_country: str) -> None:
    """
    check if we have already a feed with the sanem authorityCountry
    if yes, we set the feed to ignore to use our custom feed

    :param authority_country: the country to override
    :return: None
    """

    for i in aggregated_feed_object["sources"]:
        # print(i['source']['authorityCountry'])
        # check authorityCountry code and if the source is not FPAS
        if i['source']['authorityCountry'] == authority_country and i["source"]["feedSource"] != "FPAS":
            i['source']['ignore'] = True
            # print("Found entry to override. Set ignore to True")


def parse_one_custom_feed(data: json):
    if data['source']['override']:
        authority_country: str = data['source']["authorityCountry"]
        # check if we have to override
        check_if_we_have_an_override(authority_country)

    append_one_feed_to_json_list(data)


def parse_feeds_and_create_new_json():
    """
    parse all feed sources and merge all feeds in a new file
    :return: None
    """
    alert_hub_feeds: json = get_alert_hub_feeds()
    fpas_feeds: json = get_fpas_feeds()

    aggregated_feed_object["version"] = version_code
    aggregated_feed_object["sources"] = []

    for i in alert_hub_feeds['sources']:
        parse_one_alert_hub_feed(i)

    for j in fpas_feeds['sources']:
        parse_one_custom_feed(j)

    write_json_file()


# check if a reload is needed and if yes rewrite the aggregated_feeds.json file
if reload_feed_source:
    parse_feeds_and_create_new_json()
