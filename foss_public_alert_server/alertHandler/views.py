# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from celery import shared_task
from django.shortcuts import render

from json import loads
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotFound,
                         HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse)
from django.contrib.gis.geos import Polygon

from .models import Alert
from subscriptionHandler.models import Subscription # has to be so because of django


def get_alert_cap_data(request, identifier):
    print("Get alert Data for" + str(identifier))
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')
    try:
        a = Alert.objects.get(id=identifier)
    except Exception as e: # @todo use other exception type
        return HttpResponseNotFound('no such alert')

    # server xml files to client
    if a.cap_data:
        return HttpResponsePermanentRedirect(a.cap_data.url)

    return HttpResponseBadRequest('alert without CAP data?')


def get_alerts_for_subscription_id(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('wrong HTTP method')

    try:
        data = loads(request.body)
        subscription_id = data['subscription_id']
        subscription = Subscription.objects.get(id=subscription_id)
        polygon = subscription.bounding_box

    except (ValueError, TypeError):
        return HttpResponseBadRequest("no valid subscription")

    # filter and return all alerts which intersects with the subscribed polygone
    result = []
    for alert in Alert.objects.filter(bounding_box__intersects=polygon):
        result.append(str(alert.id))

    return JsonResponse(result, safe=False)


def debug(request):
    try:
        # fetch_alert_sources()
        output = "success"
    except Exception as e:
        print("Something went wrong" + str(e))
        output = str(e)

    return HttpResponse(output)


def index(request):
    """
    print("Test push notification")
    for alert in Alert.objects.all():
        for subscription in Subscription.objects.filter(bounding_box__intersects=alert.bounding_box):
            print(f"Send notification for {subscription.id} to {subscription.distributor_url}")
            requests.post(subscription.distributor_url, json.dumps(alert.alert_id))
    """
    return HttpResponse("Hello World")


def get_alerts_for_area(request):
    """
    get all alerts for the given area
    :param request:
    :return:
    """
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')

    try:
        y1 = float(request.GET.get('min_lat'))
        y2 = float(request.GET.get('max_lat'))
        x1 = float(request.GET.get('min_lon'))
        x2 = float(request.GET.get('max_lon'))
        if not isValidBbox(x1, y1, x2, y2):
            return HttpResponseBadRequest('invalid bounding box')
        request_bbox = Polygon.from_bbox((x1, y1, x2, y2))
    except (ValueError, TypeError):
        return HttpResponseBadRequest('invalid bounding box')

    res = []
    for alert in Alert.objects.filter(bbox__intersects=request_bbox):
        res.append(str(alert.id))
    return JsonResponse(res, safe=False)


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
