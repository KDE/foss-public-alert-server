# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests
from django.http import HttpResponseBadRequest
from requests import Response
import json

def send_notification(distributor_url, payload) -> Response:
    request = requests.post(distributor_url, json.dumps(payload))
    return request

def update_subscription(data):
    # @TODO: Implement
    return HttpResponseBadRequest("Not implemented yet")