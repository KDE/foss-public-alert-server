from django.shortcuts import render
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseNotFound,
                         HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse)

from .models import CAPFeedSource
import datetime
# Create your views here.


def generate_source_status_page(request):
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

def index(request):
    return HttpResponseRedirect("status")