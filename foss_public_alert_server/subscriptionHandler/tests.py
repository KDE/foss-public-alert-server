# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import requests
import json
import logging

from django.test import TestCase
from django.test import Client
from django.conf import settings

from alertHandler.models import Alert
from .models import Subscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SubscriptionHandlerTestsCase(TestCase):
    # @todo throws errors
    client = Client()

    def test_successful_subscription(self):
        data = {
            'min_lat': 52.295,
            'max_lat': 52.789,
            'min_lon': 8.591,
            'max_lon': 12.063,
            'distributor_url': 'https://ntfy.sh/Fg4FZIJsPe5f4nzC'
        }
        response = self.client.post('/subscription/subscribe', data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Successfully subscribed')

    def test_invalid_parameters(self):
        data = {
            'min_lat': 52.295,
            'max_lat': 52.789,
            #'min_lon': 8.591, missing
            'max_lon': 12.063,
            'distributor_url': 'https://ntfy.sh/Fg4FZIJsPe5f4nzC'
        }
        response = self.client.post('/subscription/subscribe', data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'invalid or missing parameters')

    def test_send_notification(self):
        for alert in Alert.objects.all():
            for subscription in Subscription.objects.filter(bounding_box__intersects=alert.bounding_box):
                logger.debug(f"Send notification for {subscription.id} to {subscription.distributor_url}")
                requests.post(subscription.distributor_url, json.dumps(alert.alert_id))
        # @todo check performance


def make_http_request(url, data):
    headers = {'Content-Type': 'application/json'}
    return requests.post(url, data=json.dumps(data), headers=headers)


def test_successful_subscription():
    url = 'http://127.0.0.1:8000/subscription/subscribe'
    data = {
        'min_lat': 52.295,
        'max_lat': 52.789,
        'min_lon': 8.591,
        'max_lon': 12.063,
        'distributor_url': 'https://ntfy.sh/Fg4FZIJsPe5f4nzC'
    }
    response = make_http_request(url, data)
    return response.content


# test for missing parameters
def test_subscription_missing_parameter():
    url = 'http://127.0.0.1:8000/subscription/subscribe'
    data = {
        'min_lat': 52.295,
        'max_lat': 52.789,
        #'min_lon': 8.591, missing
        'max_lon': 12.063,
        'distributor_url': 'https://ntfy.sh/Fg4FZIJsPe5f4nzC'
    }
    response = make_http_request(url, data)
    return response.content

# test_successful_subscription()
