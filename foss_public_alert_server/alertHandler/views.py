from json import loads
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotFound,
                         HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse)

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
