# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.http.request import HttpRequest
from django.shortcuts import render

from json import loads
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotFound,
                         HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse)
from django.contrib.gis.geos import Polygon

from .models import Alert
from subscriptionHandler.models import Subscription # has to be so because of django

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_alert_cap_data(request, identifier):
    """
    get the CAP alert data. Redirects to the CAP XML file for the given alert id
    :param request:
    :param identifier: the CAP alert ID
    :return: redirect to the XML cap file
    """
    logger.info(f"Get alert Data for {str(identifier)}")
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
    """
    get all alert for the given subscription id
    :param request:
    :return: json list with all alerts for the given area
    """
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')

    try:
        subscription_id = request.GET.get('subscription_id')
        subscription = Subscription.objects.get(id=subscription_id)
        polygon = subscription.bounding_box

    except (ValueError, TypeError, ObjectDoesNotExist):
        return HttpResponseBadRequest("no valid subscription")

    # filter and return all alerts which intersects with the subscribed polygone
    result = []
    for alert in Alert.objects.filter(bounding_box__intersects=polygon):
        result.append(str(alert.id))

    return JsonResponse(result, safe=False)


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

        res = []
        for alert in Alert.objects.filter(bounding_box__intersects=request_bbox):
            res.append(str(alert.id))
        return JsonResponse(res, safe=False)
    except (ValueError, TypeError):
        return HttpResponseBadRequest('invalid bounding box')


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


def alert_map(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')
    return render(request, 'map.html')
