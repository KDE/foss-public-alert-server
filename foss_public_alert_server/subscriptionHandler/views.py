# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import datetime
import json
from json import loads

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpResponse, Http404, HttpResponseBadRequest, JsonResponse
from django.contrib.gis.geos import Polygon

from .models import Subscription
from .exceptions import *
from .push_notification_services import unified_push, unified_push_encrpted, apn, firebase
from configuration.models import AppSetting

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def isValidBbox(x1, y1, x2, y2):
    """
    check if the given BBox is valid
    :param x1:
    :param y1:
    :param x2:
    :param y2:
    :return:
    """
    return (-180.0 <= x1 <= 180.0 and
            -180.0 <= x2 <= 180.0 and
            -90.0 <= y1 <= 90.0 and
            -90.0 <= y2 <= 90.0 and
            x1 != x2 and
            y1 != y2)

def is_active_subscription_update_heartbeat(subscription_id) -> bool:
    """
    check if the subscription is still active. If yes, update the last heartbeat for this subscription
    :param subscription_id: the subscription id to check
    :return: True if the subscription is active, False if the subscription is already deleted
    """
    try:
        Subscription.objects.get(id=subscription_id)
        # update last heartbeat
        Subscription.objects.filter(id=subscription_id).update(last_heartbeat=datetime.datetime.now())
        return True
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        logger.error(f"Can not update subscription: {e}")
        return False


def index(request):
    return HttpResponse("Hello World")


def subscribe(request):
    """
    subscribe to an area on the world to receive push notifications
    :param request:
    :return: HttpResponseBadRequest if request was not successful or JsonResponse if the subscription was successful
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('wrong HTTP method')

    try:
        data = loads(request.body)

        # check if request has the right parameter
        if ('min_lat' not in data or
                'max_lat' not in data or
                'min_lon' not in data or
                'max_lon' not in data or
                'token' not in data or
                'push_service' not in data):
            return HttpResponseBadRequest('invalid or missing parameters')

        # load data from request
        min_lat = float(data['min_lat'])
        max_lat = float(data['max_lat'])
        min_lon = float(data['min_lon'])
        max_lon = float(data['max_lon'])
        push_service = data['push_service']
        token = data['token']

        if AppSetting.get(f"SUPPORT_{push_service}"):
            logger.debug(f"Push Service {push_service} is supported by this server")
        else:
            return HttpResponseBadRequest('This push service is not available on this instance. '
                                          'Please try a different service')

        if not isValidBbox(min_lon, min_lat, max_lon, max_lat):
            return HttpResponseBadRequest('invalid bounding box')

        bbox = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))
        s = Subscription(token=token, bounding_box=bbox, push_service=Subscription.PushServices[push_service],
                         last_heartbeat=datetime.datetime.now())

        # send confirmation message via the push system to verify it. Only store the new subscription,
        # if the push service is reachable
        test_push = None

        match push_service:
            case "UNIFIED_PUSH":
                test_push = unified_push.send_notification(s.token, json.dumps("successfully subscribed"))
            case "UNIFIED_PUSH_ENCRYPTED":
                test_push = unified_push_encrpted.send_notification(s.token,
                                                                    json.dumps("successfully subscribed"),
                                                                    None)
            case "APN":
                test_push = apn.send_notification(s.token,
                                                  "successfully subscribed",
                                                  "",
                                                  "",
                                                  "",
                                                  "")
            case "FIREBASE":
                test_push = firebase.send_notification(s.token, json.dumps("successfully subscribed") )

        if test_push is not None and 200 <= test_push.status_code <= 299:
            s.save()
        else:
            raise PushNotificationCheckFailed("push config is invalid")

        # successfully subscribed, return success token and subscription id
        return JsonResponse({'token': 'successfully subscribed', 'id': s.id})

    except PushNotificationCheckFailed as e:
        logger.debug(f"invalid push config: {e}")
        return HttpResponseBadRequest('push service is invalid or not reachable. Please check your push notification '
                                      'server')
    except Exception as e:
        logger.debug(f"invalid request: {e}")
        return HttpResponseBadRequest('invalid request')


def unsubscribe(request):
    """
    deletes the subscriptions with the `subscription_id` from the database
    :param request:
    :return:
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('wrong HTTP method')
    try:
        data = loads(request.body)
        if "subscription_id" not in data:
            return HttpResponseBadRequest('invalid or missing parameters')
        subscription_id = data['subscription_id']
        subscription = Subscription.objects.get(id=subscription_id)
        subscription.delete()
        return HttpResponse("successfully unsubscribed")
    except ValidationError:
        return HttpResponseBadRequest("invalid subscription id")

def update_subscription(request):
    """
    depending on the type of push_service they are different needs to maintain the push notification connection
    this methode calls the corresponding methode for the different push services
    :param request: the HTTP request
    :return: HTTP response
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('wrong HTTP method')
    data = loads(request.body)

    # check parameter of request
    if 'push_service' not in data or 'subscription_id' not in data:
        return HttpResponseBadRequest('invalid or missing parameters')
    subscription_id = data['subscription_id']
    push_service = data['push_service']

    # check if subscription is still active
    if not is_active_subscription_update_heartbeat(subscription_id):
        return HttpResponseBadRequest("Subscription has expired. You must register again!")

    # check if push_service is supported
    if not AppSetting.get(f"SUPPORT_{push_service}") or AppSetting.get(f"SUPPORT_{push_service}") is None:
        return HttpResponseBadRequest('unsupported push service')

    # call the push notification handler
    match push_service:
        case "UnifiedPush":
            unified_push.update_subscription(request)
        case "UnifiedPush_encrypted":
            unified_push_encrpted.update_subscription(request)
        case "APN":
            return apn.update_subscription(request)
        case "Firebase":
            return firebase.update_subscription(request)
        case _:
            logger.debug("Not supported push service")
            return HttpResponseBadRequest('something went wrong')

def heartbeat(request):
    """
    updates the last heartbeat for the subscription
    :param request:
    :return:
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('wrong HTTP method')
    data = loads(request.body)
    # check if request contains a subscription id
    if "subscription_id" not in data:
        return HttpResponseBadRequest('invalid or missing parameters')
    subscription_id = data['subscription_id']

    if is_active_subscription_update_heartbeat(subscription_id):
        return HttpResponse("subscription successfully renewed")
    else:
        return HttpResponseBadRequest("Subscription has expired. You must register again!")