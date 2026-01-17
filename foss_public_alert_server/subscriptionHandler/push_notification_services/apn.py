# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest
from ..models import Subscription
from datetime import datetime, timezone

from django.conf import settings

apn_url_production = 'api.push.apple.com:443'
apn_url_development = 'api.sandbox.push.apple.com:443'

def create_subscription():
    raise Exception("Not implemented yet")

def send_notification(token, title, subtitle, body, category, provider_token):
    """
    @TODO implement
    :param token:
    :param title:
    :param subtitle:
    :param body:
    :param category:
    :param provider_token:
    :return:
    """
    raise Exception("Not implemented yet")

    if settings.DEBUG:
        host = apn_url_development
    else:
        host = apn_url_production

    headers = {
        ":method": "POST",
        ":scheme": "https",
        ":path": f"/3/device/{token}",
        "host": f"{host}",
        "authorization": f"bearer {provider_token}",
        #"apns-id": "",
        "apns-push-type": "alert",
        "apns-expiration": "3600", # time in seconds
        "apns-priority": "10",
        #"apns-topic": "com.example.MyApp"
    }
    json_payload = {
                   "aps" : {
                      "alert" : {
                         "title" : {title},
                         "subtitle" : {subtitle},
                         "body" : {body}
                      },
                      "category" : {category}
                   },
                }

    response = requests.post(host, headers=headers, json=json_payload)
    return response


def update_subscription(data):
    """
    @TODO implement
    :param data:
    :return:
    """
    return HttpResponseBadRequest("Not implemented yet")

    if "token" not in data or 'subscription_id' not in data:
        return HttpResponseBadRequest('invalid or missing parameters')
    token = data['token']
    subscription_id = data['subscription_id']
    try:
        Subscription.objects.get(id=subscription_id).update(token=token, last_heartbeat=datetime.now(timezone.utc))
    except ObjectDoesNotExist:
        HttpResponseBadRequest("Subscription has expired. You must register again!")
