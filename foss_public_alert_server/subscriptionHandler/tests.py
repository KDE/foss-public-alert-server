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
    fixtures = ["appSettingsDump.json"]

    client = Client()

    def test_successful_subscription(self):
        data = {
            'min_lat': 52.295,
            'max_lat': 52.789,
            'min_lon': 8.591,
            'max_lon': 12.063,
            "push_service": "UNIFIED_PUSH",
            'token': 'https://unifiedpush.kde.org/J9gTXxwbOEKNfeJW'
        }
        response = self.client.post('/subscription/', json.dumps(data), content_type="application/json")
        self.assertContains(response, 'successfully subscribed', status_code=200)

    def test_successful_unsubscribe(self):
        data = {
            'min_lat': 52.295,
            'max_lat': 52.789,
            'min_lon': 8.591,
            'max_lon': 12.063,
            "push_service": "UNIFIED_PUSH",
            'token': 'https://unifiedpush.kde.org/J9gTXxwbOEKNfeJW'
        }
        response = self.client.post('/subscription/', json.dumps(data), content_type="application/json")
        data = json.loads(response.content)
        subscription_id = data["subscription_id"]

        response = self.client.delete(f'/subscription/?subscription_id={subscription_id}', content_type="application/json")
        self.assertContains(response, 'successfully unsubscribed', status_code=200)

    def test_unsuccessful_unsubscribe_invalid_subscription_id(self):
        response = self.client.delete('/subscription/?subscription_id=invalid_id', content_type="application/json")
        self.assertContains(response, 'invalid subscription id', status_code=400)

    def test_push_service_not_supported(self):
        data = {
            'min_lat': 52.295,
            'max_lat': 52.789,
            'min_lon': 8.591,
            'max_lon': 12.063,
            "push_service": "EXAMPLE_PUSH",
            'token': 'https://example.com'
        }
        response = self.client.post('/subscription/', json.dumps(data), content_type="application/json")
        self.assertContains(response, b'push service is not available on this instance.', status_code=400)

    def test_blocked_unifiedPush(self):
        data = {
            'min_lat': 52.295,
            'max_lat': 52.789,
            'min_lon': 8.591,
            'max_lon': 12.063,
            "push_service": "UNIFIED_PUSH",
            'token': 'https://ntfy.sh/J9gTXxwbOEKNfeJW'
        }
        response = self.client.post('/subscription/', data, content_type="application/json")
        self.assertContains(response, b'Your UnifiedPush Server ntfy.sh is blocked. We can not reliably deliver push notifications to this server. Please choose another one.', status_code=400)

    def test_antimeridian_cross(self):
        data = {
            'min_lat': 179.0,
            'max_lat': -179.0,
            'min_lon': 8.591,
            'max_lon': 12.063,
            "push_service": "UNIFIED_PUSH",
            'token': 'https://unifiedpush.kde.org/J9gTXxwbOEKNfeJW'
        }
        response = self.client.post('/subscription/', data, content_type="application/json")
        self.assertContains(response, b'invalid bounding box', status_code=400)

    def test_invalid_parameters(self):
        data = {
            'min_lat': 52.295,
            'max_lat': 52.789,
            #'min_lon': 8.591, missing
            'max_lon': 12.063,
            "push_service": "UNIFIED_PUSH",
            'token': 'https://unifiedpush.kde.org/J9gTXxwbOEKNfeJW'
        }
        response = self.client.post('/subscription/', data, content_type="application/json")
        self.assertContains(response, b'invalid or missing parameters', status_code=400)

    def test_send_notification(self):
        for alert in Alert.objects.all():
            for subscription in Subscription.objects.filter(bounding_box__intersects=alert.area):
                logger.debug(f"Send notification for {subscription.id} to {subscription.distributor_url}")
                requests.post(subscription.token, json.dumps(alert.alert_id)) #@todo fix
        # @todo check performance

    def test_update_subscription_sent_heartbeat(self):
        # create subscription
        data = {
            'min_lat': 52.295,
            'max_lat': 52.789,
            'min_lon': 8.591,
            'max_lon': 12.063,
            "push_service": "UNIFIED_PUSH",
            'token': 'https://unifiedpush.kde.org/J9gTXxwbOEKNfeJW'
        }
        response = self.client.post('/subscription/', json.dumps(data), content_type="application/json")
        data = json.loads(response.content)
        subscription_id = data["subscription_id"]
        # update subscription
        response = self.client.put(f'/subscription/?subscription_id={subscription_id}')
        self.assertContains(response, 'Subscription successfully updated', status_code=200)

    def test_update_subscription_invalid_subscription_id(self):
        response = self.client.put(f'/subscription/?subscription_id=invalid',
                                   content_type="application/json")
        self.assertContains(response, 'invalid input', status_code=400)

    def test_update_subscription_old_subscription_id(self):
        response = self.client.put(f'/subscription/?subscription_id=e1ce46fb-a885-4b26-5ba8-708cccfcfa2b',
                                   content_type="application/json")
        self.assertContains(response, 'Subscription has expired. You must register again!', status_code=404)