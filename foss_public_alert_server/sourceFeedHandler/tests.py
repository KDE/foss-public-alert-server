# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from django.test import TestCase, RequestFactory, Client
from django.http.request import HttpRequest
from .views import get_feed_status_for_area

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SourceFeedHandlerTestsCase(TestCase):
    fixtures = ["sourceFeedHandlerDump.json"]
    client = Client()

    def test_get_feed_status_for_area(self):
        response =  self.client.get("/sources/area_status?country_codes=de&country_codes=fr")

        expected_response = (b'{"results": [{"name": "Deutschland: Landeshochwasserportal", "source_is_official": '
                             b'true, "cap_alert_feed_status": "operating", "authorityCountry": "de", "register_url": '
                             b'null, "latest_published_alert_datetime": null}, {"name": "Deutschland: Biwapp", '
                             b'"source_is_official": true, "cap_alert_feed_status": "operating", "authorityCountry": '
                             b'"de", "register_url": null, "latest_published_alert_datetime": null}, '
                             b'{"name": "Deutschland: Bundesamt f\\u00fcr Bev\\u00f6lkerungschutz und '
                             b'Katastrophenhilfe", "source_is_official": true, "cap_alert_feed_status": "operating", '
                             b'"authorityCountry": "de", "register_url": null, "latest_published_alert_datetime": '
                             b'"2024-12-10T06:34:18Z"}, {"name": "Deutschland: Deutscher Wetterdienst", '
                             b'"source_is_official": true, "cap_alert_feed_status": "operating", "authorityCountry": '
                             b'"de", "register_url": null, "latest_published_alert_datetime": null}, '
                             b'{"name": "France: Meteo-France", "source_is_official": true, "cap_alert_feed_status": '
                             b'"operating", "authorityCountry": "fr", "register_url": '
                             b'"https://alertingauthority.wmo.int/authorities.php?recId=53", '
                             b'"latest_published_alert_datetime": "2024-12-10T05:00:44Z"}]}')

        self.assertEqual(response.content, expected_response)

    def test_get_feed_status_for_area_no_feeds_for_area(self):
        response = self.client.get("/sources/area_status?country_codes=invalid")

        self.assertContains(response, b'{"results": []}', status_code=200)

    def test_get_feed_status_for_area_invalid_parameter(self):
        response = self.client.get("/sources/area_status?invalid=de")

        self.assertContains(response,"invalid input", status_code=400)

    def test_get_feed_status_for_area_invalid_parameter_empty_list(self):
        response = self.client.get("/sources/area_status?country_codes=")

        self.assertContains(response, "invalid input", status_code=400)

    def test_get_feed_status_for_area_wrong_http_method(self):
        data = {
            'invalid': "None"
        }

        response = self.client.post("/sources/area_status", data)

        self.assertContains(response,"wrong HTTP method", status_code=400)