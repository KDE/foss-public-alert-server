# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import datetime
import json
import uuid
from json import loads

from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseNotFound
from django.contrib.gis.geos import Polygon
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

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

@csrf_exempt
@require_http_methods(["POST", "DELETE", "PUT", "GET"])
def subscribe(request):
    """
    call handler for POST, DELETE or PUT request
    :param request:
    :return:
    """
    if request.method == "POST":
        return add_new_subscription(request)
    elif request.method == 'DELETE':
        return unsubscribe(request)
    elif request.method == 'PUT':
        return update_subscription(request)
    elif request.method == 'GET':
        return handle_subscription_config_request(request)
    else:
        return HttpResponseBadRequest("Invalid HTTP method")

@require_http_methods(["POST"])
def add_new_subscription(request):
    """
    subscribe to an area on the world to receive push notifications
    :param request:
    :return: HttpResponseBadRequest if request was not successful or JsonResponse if the subscription was successful
    """
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

        # send confirmation message via the push system to verify it. Only store the new subscription,
        # if the push service is reachable
        test_push = None
        s = None

        confirmation_id = str(uuid.uuid4())
        msg = {}
        msg['type'] = 'subscribe'
        msg['message'] = "successfully subscribed"
        msg['confirmation_id'] = confirmation_id

        match push_service:
            case "UNIFIED_PUSH":
                s = unified_push.create_subscription(token, bbox)
                test_push = unified_push.send_notification(s.token, json.dumps(msg))
            case "UNIFIED_PUSH_ENCRYPTED":
                s = unified_push_encrpted.create_subscription(token, bbox, data)
                test_push = unified_push_encrpted.send_notification(s.token,
                                                    json.dumps(msg),
                                                    auth_key=s.auth_key,
                                                    p256dh_key=s.p256dh_key)
            case "APN":
                s = apn.create_subscription()
                test_push = apn.send_notification(s.token,
                                                  json.dumps(msg),
                                                  "",
                                                  "",
                                                  "",
                                                  "")
            case "FIREBASE":
                s = firebase.create_subscription()
                test_push = firebase.send_notification(s.token, json.dumps(msg))

        if test_push is not None and 200 <= test_push.status_code <= 299 and s is not None:
            s.save()
        else:
            raise PushNotificationCheckFailed("push config is invalid")

        # successfully subscribed, return success token and subscription id
        return JsonResponse({
            'token': 'successfully subscribed',
            'subscription_id': s.id,
            'confirmation_id': confirmation_id
        })

    except (PushNotificationCheckFailed, PushNotificationException) as e:
        logger.debug(f"invalid push config: {e}")
        return HttpResponseBadRequest('push service is invalid or not reachable. Please check your push notification '
                                      'server')
    except Exception as e:
        logger.debug(f"invalid request: {e}")
        return HttpResponseBadRequest('invalid request')


@require_http_methods(['DELETE'])
def unsubscribe(request):
    """
    deletes the subscriptions with the `subscription_id` from the database
    :param request:
    :return:
    """
    try:
        subscription_id = request.GET.get('subscription_id')
        subscription = Subscription.objects.get(id=subscription_id)
        subscription.delete()
        return HttpResponse("successfully unsubscribed")
    except ValidationError:
        return HttpResponseBadRequest("invalid subscription id")

@require_http_methods(["PUT"])
def update_subscription(request):
    """
    depending on the type of push_service they are different needs to maintain the push notification connection
    this methode calls the corresponding methode for the different push services
    :param request: the HTTP request
    :return: HTTP response
    """
    # check parameter of request
    subscription_id = request.GET.get('subscription_id')

    if subscription_id is None:
        return HttpResponseBadRequest('invalid or missing parameters')

    # check if subscription is still active
    try:
        if Subscription.objects.filter(id=subscription_id).update(last_heartbeat=datetime.datetime.now()) == 0:
            return HttpResponseNotFound("Subscription has expired. You must register again!")
    except Exception as e:
        logger.error(f"Can not update subscription: {e}")
        return HttpResponseBadRequest("invalid input")

    # if request contains token, handle update request
    token = request.GET.get("token")

    if token is None:
        # if token is none, the request is just to update the subscription
        return HttpResponse("Subscription successfully updated")
    else:
        # get selected push service as human-readable label
        push_service = Subscription.objects.get(id=subscription_id).get_push_service_display()

        # check if push_service is supported
        if not AppSetting.get(f"SUPPORT_{push_service}") or AppSetting.get(f"SUPPORT_{push_service}") is None:
            return HttpResponseBadRequest('unsupported push service')

        # call the push notification handler
        match push_service:
            case Subscription.PushServices.UNIFIED_PUSH.name:
                unified_push.update_subscription(request)
            case Subscription.PushServices.UNIFIED_PUSH_ENCRYPTED.name:
                unified_push_encrpted.update_subscription(request)
            case Subscription.PushServices.APN.name:
                return apn.update_subscription(request)
            case Subscription.PushServices.FIREBASE.name:
                return firebase.update_subscription(request)
            case _:
                logger.debug("Not supported push service")
                return HttpResponseBadRequest('something went wrong')


@require_http_methods(["GET"])
def handle_subscription_config_request(request):
    if request.GET.get('type') == "webpush":
        return vapid_key(request)
    else:
        return HttpResponseBadRequest("invalid input")

@require_http_methods(["GET"])
def vapid_key(request)-> HttpResponse:
    """
    Let clients fetch the VAOID key needed for webpush
    :param request: the request of the client
    :return: JsonResponse with the VAPID key
    """
    return JsonResponse({'vapid-key': settings.WEB_PUSH_CONFIG_PUBLIC_KEY})