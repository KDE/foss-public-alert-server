# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http.request import HttpRequest
from django.shortcuts import render

from django.http import (HttpResponseBadRequest, HttpResponseNotFound,
                         HttpResponsePermanentRedirect, JsonResponse)
from django.contrib.gis.geos import Polygon
from django.views.decorators.http import require_http_methods

from .models import Alert
from subscriptionHandler.models import Subscription # has to be so because of django
from lib.bbox import is_valid_bbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def get_alert_cap_data(request, identifier):
    """
    get the CAP alert data. Redirects to the CAP XML file for the given alert id
    :param request:
    :param identifier: the CAP alert ID
    :return: redirect to the XML cap file
    """
    try:
        a = Alert.objects.get(id=identifier)
    except Exception as e: # @todo use other exception type
        return HttpResponseNotFound('no such alert')

    # server xml files to client
    if a.cap_data:
        return HttpResponsePermanentRedirect(a.cap_data.url)

    return HttpResponseBadRequest('alert without CAP data?')

@require_http_methods(["GET"])
def get_alerts_for_subscription_id(request):
    """
    get all alert for the given subscription id
    :param request:
    :return: json list with all alerts for the given area
    """
    try:
        subscription_id = request.GET.get('subscription_id')
        subscription = Subscription.objects.get(id=subscription_id)
        polygon = subscription.bounding_box

    except (ValueError, TypeError, ObjectDoesNotExist, ValidationError):
        return HttpResponseBadRequest("no valid subscription")

    # filter and return all alerts which intersects with the subscribed polygone
    result = []
    for alert in Alert.objects.filter(area__intersects=polygon).values_list('id', flat=True):
        result.append(str(alert))

    return JsonResponse(result, safe=False)

@require_http_methods(["GET"])
def get_alerts_for_area(request):
    """
    get all alerts for the given area
    :param request:
    :return:
    """
    try:
        y1 = float(request.GET.get('min_lat'))
        y2 = float(request.GET.get('max_lat'))
        x1 = float(request.GET.get('min_lon'))
        x2 = float(request.GET.get('max_lon'))
        if not is_valid_bbox(x1, y1, x2, y2):
            return HttpResponseBadRequest('invalid bounding box')
        request_bbox = Polygon.from_bbox((x1, y1, x2, y2))

        res = []
        # TODO(Nucleus): restrict max size of bounding box
        for alert in Alert.objects.filter(area__intersects=request_bbox).values_list('id', flat=True):
            res.append(str(alert))
        return JsonResponse(res, safe=False)
    except (ValueError, TypeError):
        return HttpResponseBadRequest('invalid bounding box')


@require_http_methods(["GET"])
def alert_map(request: HttpRequest):
    return render(request, 'map.html')
