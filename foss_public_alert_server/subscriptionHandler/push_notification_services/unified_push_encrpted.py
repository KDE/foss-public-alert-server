# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseNotFound
from pywebpush import webpush, WebPushException
from django.conf import settings
import logging
from datetime import datetime, timezone
from requests import Response, HTTPError, Session, Timeout, ConnectionError, ConnectTimeout, RequestException, ReadTimeout

from subscriptionHandler.models import Subscription
from .push_tools import checkTimeoutFlag, setTimeoutFlag

from ..exceptions import PushNotificationException, PushNotificationTimeoutException, PushNotificationExpiredException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = Session()


def create_subscription(token, bbox, data, user_agent):
    """
    create an encrypted unifiedPush subscription. This requires the additional parameter `p256dh_key` and `auth_key` in
    data
    :param token: the unifiedPush endpoint
    :param bbox: the bounding box to subscribe for
    :param data: the request data with the additional parameter p256dh_key and auth_key
    :param user_agent: the clients user agent
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
                        last_heartbeat=datetime.now(timezone.utc), p256dh_key=p256dh_key, auth_key=auth_key, user_agent=user_agent)


def send_notification(endpoint, payload, auth_key, p256dh_key, persist_failures: bool = True) -> Response or None:
    """
    Send a webpush notification to the given endpoint with the given payload
    :param endpoint: the webpush endpoint
    :param payload: the message to encrypt and send
    :param auth_key: the key to authorize ourselves against the webpush server
    :param p256dh_key: encryption key
    :param persist_failures: whether to record HTTP or network errors in the ConnectionFlag table
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

        # check if this server has a timeout flag
        checkTimeoutFlag(endpoint)

        return webpush(subscription_info,
                       payload,
                       vapid_private_key=settings.WEB_PUSH_CONFIG_PRIVATE_KEY,
                       vapid_claims=claims,
                       timeout=10,
                       requests_session=session)
    except WebPushException as e:
        logger.error(f"Failed to send web push notification due to {e}")
        resp = getattr(e, "response", None)
        if resp is not None:
            status = getattr(resp, "status_code", None)
            body = getattr(resp, "text", "")[:2000]

            match status:
                case 404 | 410:
                    # the subscription has expired and can not be used anymore.
                    # We have to delete the subscription on our side too
                    # https://datatracker.ietf.org/doc/html/rfc8030
                    raise PushNotificationExpiredException(body)
                case 429:
                    # The server responded with "too many requests" we have to wait until we try again.
                    if persist_failures:
                        setTimeoutFlag(endpoint, body)
            raise PushNotificationException(status)
        raise PushNotificationException()

    except PushNotificationTimeoutException as e:
        # do not set the timeout flag if the flag raised the exception
        logger.error(f"Failed to send web push notification due to {e}")
        raise PushNotificationException("defer")

    except (ConnectTimeout, Timeout, ConnectionError, HTTPError, ReadTimeout, RequestException, OSError) as e:
        if persist_failures:
            setTimeoutFlag(endpoint, str(e))
        logger.error(f"Failed to send web push notification due to {e}")
        if isinstance(e, ConnectTimeout) or isinstance(e, Timeout) or isinstance(e, ReadTimeout):
            raise PushNotificationException("timeout")
        raise PushNotificationException("failure")


def update_subscription(token, request, subscription_id:str) -> HttpResponse:
    """
    Update the push notification config for the given subscription.

    This allows clients to send updated configs to the server to update the config.
    We are not checking the refreshed config here with sending a push notification as we expect the setup did
    not change, but just the token. If we notice that we also check the new config before accepting, we might
    add that in the future.

    Also reset the error counter to zero as the config is refreshed.
    :param request: the http request with the p256dh_key and the auth_key
    :param token: the new UnifiedPush token for the subscription
    :param subscription_id: the id of the subscription to update
    :return: HttpResponseBadRequest if there are missing parameters / invalid input, HttpResponse if the update was successful.
    """
    p256dh_key = request.GET.get("p256dh_key")
    auth_key =  request.GET.get("auth_key")
    if p256dh_key == "" or auth_key == "":
        return HttpResponseBadRequest('invalid or missing parameters')
    try:
        Subscription.objects.filter(id=subscription_id).update(token=token, auth_key=auth_key, p256dh_key=p256dh_key)
        return HttpResponse("Subscription and push config successfully updated")
    except Exception as e:
        logger.error(f"Can not update subscription: {e}")
        return HttpResponseBadRequest("invalid input")