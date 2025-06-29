# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests
from django.http import HttpResponseBadRequest
from requests import Response, ConnectionError, HTTPError, ReadTimeout, RequestException, Timeout, ConnectTimeout
import json
import logging
from datetime import datetime

from subscriptionHandler.models import Subscription
from subscriptionHandler.exceptions import PushNotificationException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_subscription(token, bbox):
    return Subscription(token=token, bounding_box=bbox, push_service=Subscription.PushServices.UNIFIED_PUSH,
                        last_heartbeat=datetime.now())

def send_notification(distributor_url, payload:json) -> Response:
    """
    Send a notification to a legacy unifiedPush endpoint without encryption
    :raise PushNotificationException if the request failed
    """
    try:
        request = requests.post(distributor_url, payload, timeout=10)
        return request
    except (ConnectionError, HTTPError, ReadTimeout, RequestException, Timeout, ConnectTimeout):
        logger.error("Failed to send push notification")
        raise PushNotificationException

def update_subscription(data):
    # @TODO: Implement
    return HttpResponseBadRequest("Not implemented yet")