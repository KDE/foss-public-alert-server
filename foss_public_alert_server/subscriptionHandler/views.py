# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import time
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseBadRequest, JsonResponse
from django.contrib.gis.geos import Polygon
from json import loads
import datetime
import requests
import json

from .models import Subscription


# Create your views here.


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

    data = loads(request.body)

    # check if request has the right parameter
    if ('min_lat' not in data or
            'max_lat' not in data or
            'min_lon' not in data or
            'max_lon' not in data or
            'distributor_url' not in data):
        return HttpResponseBadRequest('invalid or missing parameters')

    # load data from request
    min_lat = float(data['min_lat'])
    max_lat = float(data['max_lat'])
    min_lon = float(data['min_lon'])
    max_lon = float(data['max_lon'])

    if not isValidBbox(min_lon, min_lat, max_lon, max_lat):
        return HttpResponseBadRequest('invalid bounding box')

    bbox = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))
    s = Subscription(distributor_url=data['distributor_url'], bounding_box=bbox, last_heartbeat=datetime.datetime.now())

    # send confirmation message via the distributor to verify it. Only store the new subscription,
    # if the distributor is reachable
    test_push = requests.post(s.distributor_url, json.dumps("Successfully subscribed"))
    if 200 <= test_push.status_code <= 299:
        s.save()
    else:
        return HttpResponseBadRequest('Distributor url is invalid or not reachable. Please check your unified push '
                                      'server')

    # successfully subscribed, return success token and subscription id
    return JsonResponse({'token': 'Successfully subscribed', 'id': s.id})


def unsubscribe(request):
    """
    deletes the subscriptions with the `subscription_id` from the database
    :param request:
    :return:
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('wrong HTTP method')
    data = loads(request.body)
    if "subscription_id" not in data:
        return HttpResponseBadRequest('invalid or missing parameters')
    subscription_id = data['subscription_id']
    subscription = Subscription.objects.get(id=subscription_id)
    subscription.delete()
    return HttpResponse("Successfully unsubscribed")


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
    try:
        # update last heartbeat
        Subscription.objects.filter(id=subscription_id).update(last_heartbeat=datetime.datetime.now())
    except Exception as e:  # @todo use other Exception type
        print(f"Error: {e}")
        HttpResponseBadRequest("Subscription has expired. You must register again!")

    return HttpResponse("subscription successfully renewed")
