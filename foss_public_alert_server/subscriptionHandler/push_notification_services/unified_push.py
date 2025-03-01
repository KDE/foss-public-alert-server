# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests
from django.http import HttpResponseBadRequest
from requests import Response
import json
from datetime import datetime

from subscriptionHandler.models import Subscription


def create_subscription(token, bbox):
    return Subscription(token=token, bounding_box=bbox, push_service=Subscription.PushServices.UNIFIED_PUSH,
                        last_heartbeat=datetime.now())

def send_notification(distributor_url, payload:json) -> Response:
    request = requests.post(distributor_url, payload)
    return request

def update_subscription(data):
    # @TODO: Implement
    return HttpResponseBadRequest("Not implemented yet")