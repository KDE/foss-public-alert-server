# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests
from django.http import HttpResponseBadRequest
from requests import Response, ConnectionError, HTTPError, ReadTimeout, RequestException, Timeout, ConnectTimeout
import json
import logging
from datetime import datetime, timezone

from subscriptionHandler.models import Subscription
from subscriptionHandler.exceptions import PushNotificationException, PushNotificationTimeoutException
from .push_tools import checkTimeoutFlag, setTimeoutFlag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_subscription(token, bbox, user_agent):
    return Subscription(token=token, bounding_box=bbox, push_service=Subscription.PushServices.UNIFIED_PUSH,
                        last_heartbeat=datetime.now(timezone.utc), user_agent=user_agent)


def send_notification(distributor_url, payload: json, persist_failures: bool = True) -> Response:
    """
    Send a notification to a legacy unifiedPush endpoint without encryption
    :param distributor_url: the UnifiedPush endpoint
    :param payload: the push message to send
    :param persist_failures: whether to record HTTP or network errors in the ConnectionFlag table
    :raise PushNotificationException if the request failed
    """
    try:
        checkTimeoutFlag(distributor_url)
        res = requests.post(distributor_url, payload, timeout=10)
        if res.status_code == 429:
            # rate limited
            if persist_failures:
                setTimeoutFlag(distributor_url, res.text)
        if res.status_code < 200 or res.status_code > 299:
            raise PushNotificationException(res.status_code)
        return res

    except PushNotificationTimeoutException as e:
        logger.error(f"Failed to send push notification due to {e}")
        raise PushNotificationException("defer")

    except (ConnectTimeout, Timeout, ConnectionError, HTTPError, ReadTimeout, RequestException, OSError) as e:
        if persist_failures:
            setTimeoutFlag(distributor_url, str(e))
        logger.error(f"Failed to send push notification due to {e}")
        if isinstance(e, ConnectTimeout) or isinstance(e, Timeout) or isinstance(e, ReadTimeout):
            raise PushNotificationException("timeout")
        raise PushNotificationException("failure")


def update_subscription(data):
    # @TODO: Implement
    return HttpResponseBadRequest("Not implemented yet")