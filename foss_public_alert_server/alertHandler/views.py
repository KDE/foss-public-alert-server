from celery import shared_task
from django.shortcuts import render
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotFound,
                         HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse)
from json import loads

# Create your views here.
from .models import Alert
from .tasks import fetch_alert_sources, test_celery
from subscriptionHandler.models import Subscription # has to be so because of django
from time import sleep


def get_alert_cap_data(request, identifier):
    print("Get alert Data for" + str(identifier))
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')
    try:
        a = Alert.objects.get(id=identifier)
    except Exception as e: # @todo use other exception type
        return HttpResponseNotFound('no such alert')

    if a.source_url:
        return HttpResponseRedirect(a.source_url)
    elif a.cap_data:
        return HttpResponsePermanentRedirect(a.cap_data.url)

    return HttpResponseBadRequest('alert without CAP data?')


def get_alerts_for_subscription_id(request):
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')

    try:
        data = loads(request.body)
        subscription_id = data['subscription_id']
        polygon = Subscription.objects.filter(subscription_id=subscription_id)

    except (ValueError, TypeError):
        return HttpResponseBadRequest("no valid subscription")

    # filter and return all alerts which intersects with the subscribed polygone
    result = []
    for alert in Alert.objects.filter(bounding_box__intersects=polygon):
        result.append(str(alert.id))

    return JsonResponse(result, safe=False)


def debug(request):

    try:
        fetch_alert_sources()
        output = "success"
    except Exception as e:
        print("Something went wrong" + str(e))
        output = str(e)

    return HttpResponse(output)


def index(request):
    test_celery.delay()
    return HttpResponse("Task started")
