# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from requests import Response
from django.http import HttpResponseBadRequest
from pywebpush import webpush, WebPushException
from django.conf import settings
import logging
from datetime import datetime

from subscriptionHandler.models import Subscription

from ..exceptions import PushNotificationException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_subscription(token, bbox, data):
    """
    create an encrypted unifiePush subscription. This requires the additional parameter `p256dh_key` and `auth_key` in
    data
    :param token: the unifiedPush endpoint
    :param bbox: the bounding box to subscribe for
    :param data: the request data with the additional parameter p256dh_key and auth_key
    :return: a new subscription of type UNIFIED_PUSH_ENCRYPTED
    """
    if ('p256dh_key' not in data or
            'auth_key' not in data):
        return HttpResponseBadRequest('invalid or missing parameters')

    # load data from request
    p256dh_key = data['p256dh_key']
    auth_key = data['auth_key']

    if p256dh_key == "" or auth_key == "":
        return HttpResponseBadRequest('invalid or missing parameters')

    return Subscription(token=token, bounding_box=bbox, push_service=Subscription.PushServices.UNIFIED_PUSH_ENCRYPTED,
                        last_heartbeat=datetime.now(), p256dh_key=p256dh_key, auth_key=auth_key)


def send_notification(endpoint, payload, auth_key, p256dh_key) -> Response or None:
    """
    Send a webpush notification to the given endpoint with the given payload
    :param endpoint: the webpush endpoint
    :param payload: the message to encrypt and send
    :param auth_key: the key to authorize ourselves against the webpush server
    :param p256dh_key: encryption key
    :return: Response if successful
    :raise: PushNotificationException if the request failed
    """
    try:
        subscription_info = {
            "endpoint": endpoint,
            "keys": {
                "auth": auth_key,
                "p256dh": p256dh_key
            }
        }

        # web push claims
        # aud: The “audience” is the destination URL of the push service.
        # exp: The “expiration” date is the UTC time in seconds when the claim should expire. (not more than 24h
        # sub: The “subscriber” is the primary contact email for this subscription.
        claims = {
            "sub": settings.WEB_PUSH_CONTACT,
            "exp": round(datetime.now().second + 86400)  # now + 24h
        }

        return webpush(subscription_info,
                       payload,
                       vapid_private_key=settings.WEB_PUSH_CONFIG_PRIVATE_KEY,
                       vapid_claims=claims,
                       timeout=10)
    except WebPushException as e:
        logger.error("Failed to send web push notification")
        raise PushNotificationException()


def update_subscription(data):
    # @TODO: Implement
    return HttpResponseBadRequest("Not implemented yet")