# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseBadRequest, JsonResponse
from django.contrib.gis.geos import Polygon
from json import loads
import datetime

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
    :return:
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('wrong HTTP method')

    data = loads(request.body)
    min_lat = float(data['min_lat'])
    max_lat = float(data['max_lat'])
    min_lon = float(data['min_lon'])
    max_lon = float(data['max_lon'])
    if not isValidBbox(min_lon, min_lat, max_lon, max_lat):
        return HttpResponseBadRequest('invalid bounding box')

    bbox = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))
    s = Subscription(distributor_url=data['distributor_url'], bbox=bbox)
    s.save()
    # @todo send test message via the distributor to verify it
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
    subscription_id = data['subscription_id']
    subscription = Subscription.objects.get(subscription_id=subscription_id)
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
    subscription_id = data['subscription_id']
    try:
        subscription = Subscription.objects.get(subscription_id=subscription_id)
        # update last heartbeat
        subscription.last_heartbeat = datetime.datetime.now()
        subscription.save()
    except Exception as e: # @todo use other Exception type
        print(f"Error: {e}")
        HttpResponseBadRequest("Subscription has expired. You must register again!")

    return HttpResponse("subscription successfully renewed")
