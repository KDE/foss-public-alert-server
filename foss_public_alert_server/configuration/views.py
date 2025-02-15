# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later
import os

from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.conf import settings

from .models import AppSetting

def version_string() -> str:
    """
    build the version string. If the server is not in debug mode, append build-revision to version code
    :return: the version code with build revision or debug tag
    """
    version = AppSetting.get("VERSION")
    if not settings.DEBUG:
        revision_file = os.path.join(settings.BASE_DIR, "build-revision")
        with open(revision_file, 'r') as f:
            rev = f.read()
            version = f"{version} ({rev})"
    else:
        version = f"{version} (DEBUG)"
    return version

def get_server_status(request:HttpRequest):
    """
    endpoint to check the server status. This methode can be used to get information about privacy, ToS
    :param request: client request to get the data
    :return: `server_version`: the installed server version
            `server_operator`: the organisation that operates the server instance
            `privacy_notice`: URL to the privacy police of the server
            `terms_of_service`: URL to the terms of service
            `congestion_state`: int value to determine the load the of the server, if this value is too high, the
            client should use a different server instance
            `supported_push_services`: list of push services that are supported by this server instance

    """
    if request.method != "GET":
        return HttpResponseBadRequest("wrong HTTP method")

    result = {
        "server_version": version_string(),
        "server_operator": AppSetting.get("OPERATOR"),
        "privacy_notice": AppSetting.get("PRIVACY_NOTICE"),
        "terms_of_service": AppSetting.get("TERMS_OF_SERVICE"),
        "congestion_state": AppSetting.get("CONGESTION_STATE"),
        "supported_push_services": {"UNIFIED_PUSH": AppSetting.get("SUPPORT_UNIFIED_PUSH"),
                                    "UNIFIED_PUSH_ENCRYPTED" : AppSetting.get("SUPPORT_UNIFIED_PUSH_ENCRYPTED"),
                                    "APN" : AppSetting.get("SUPPORT_APN"),
                                    "FIREBASE": AppSetting.get("SUPPORT_FIREBASE")}
    }
    return JsonResponse(result)

def index(request):
    """
    show server information page
    """
    if request.method != 'GET':
        return HttpResponseBadRequest('wrong HTTP method')

    context = {
        'version': version_string()
    }

    return render(request, 'server_info.html', context=context)
