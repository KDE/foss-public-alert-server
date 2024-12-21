# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.shortcuts import render
from django.http.request import HttpRequest
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotFound,
                         HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse)

from json import loads
from .models import CAPFeedSource
import datetime
from django.conf import settings
# Create your views here.


def generate_source_status_page(request:HttpRequest):
    """
    generate a status page for every CapSource
    :param request:
    :return: a HTML page with an overview of all cap source feed and the last fetch status
    """
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')

    number_of_source = CAPFeedSource.objects.all().count()

    context = {
        'number_of_sources': number_of_source,
        'list_of_sources': CAPFeedSource.objects.all().order_by('source_id'),
        'datetime':  datetime.datetime.now() #@todo fix timezone
    }

    return render(request, 'source_status_page.html', context=context)


def get_feed_status_for_area(request:HttpRequest):
    """
    return the feeds for the given country code
    :param request: the http POST request a list of country codes as parameter 'country_code': [list]
    :return: a list of feeds with this country code
    """
    if request.method != "POST":
        return HttpResponseBadRequest("wrong HTTP method")


    try:
        data:list = request.POST.getlist('country_codes', None)
    except ValueError:
        return HttpResponseBadRequest('invalid parameters')

    # check if the request contained valid data
    if len(data) == 0:
        return HttpResponseBadRequest('invalid parameters')

    result = {'results': []}

    for code in data:
        for entry in CAPFeedSource.objects.filter(authorityCountry=code):
            temp_result = {"name": entry.name,
                           "source_is_official": entry.source_is_official,
                           "cap_alert_feed_status": entry.cap_alert_feed_status,
                           "authorityCountry": entry.authorityCountry,
                           "register_url": entry.register_url,
                           "latest_published_alert_datetime" : entry.latest_published_alert_datetime
                           }
            result['results'].append(temp_result)

    return JsonResponse(result, safe=False)

def server_status(request:HttpRequest):
    """
    endpoint to check the server status
    :param request:
    :return:
    """
    if request.method != "GET":
        return HttpResponseBadRequest("wrong HTTP method")

    result = {
        "server_version": settings.SERVER_VERSION,
        "server_operator": settings.OPERATOR,
        "privacy_notice": settings.PRIVACY_NOTICE,
        "terms_of_service": settings.TERMS_OF_SERVICE,
        "congestion_state": settings.CONGESTION_STATE
    }
    return JsonResponse(result)

def index(request):
    """
    show server information page
    """
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')

    context = {
        'version': settings.SERVER_VERSION
    }

    return render(request, 'server_info.html', context=context)
