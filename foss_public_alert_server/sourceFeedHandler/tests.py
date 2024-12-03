# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.test import TestCase, RequestFactory
from django.http.request import HttpRequest
from .views import get_feed_status_for_area


class SourceFeedHandlerTestsCase(TestCase):
    fixtures = ["sourceFeedHandlerDump.json"]

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_feed_status_for_area(self):
        data = {
            'country_codes': ['de', 'fr']
        }

        request: HttpRequest = self.factory.post("/sources/area_status", data)

        response = get_feed_status_for_area(request)

        expected_response = (b'{"results": [{"name": "Deutschland: Landeshochwasserportal", "source_is_official": '
                             b'true, "cap_alert_feed_status": "operating", "authorityCountry": "de", "register_url": '
                             b'null}, {"name": "Deutschland: Bundesamt f\\u00fcr Bev\\u00f6lkerungschutz und '
                             b'Katastrophenhilfe", "source_is_official": true, "cap_alert_feed_status": "operating", '
                             b'"authorityCountry": "de", "register_url": null}, {"name": "Deutschland: Biwapp", '
                             b'"source_is_official": true, "cap_alert_feed_status": "operating", "authorityCountry": '
                             b'"de", "register_url": null}, {"name": "Deutschland: Deutscher Wetterdienst", '
                             b'"source_is_official": true, "cap_alert_feed_status": "operating", "authorityCountry": '
                             b'"de", "register_url": null}, {"name": "France: Meteo-France", "source_is_official": '
                             b'true, "cap_alert_feed_status": "operating", "authorityCountry": "fr", "register_url": '
                             b'"https://alertingauthority.wmo.int/authorities.php?recId=53"}]}')

        self.assertEqual(response.content, expected_response)

    def test_get_feed_status_for_area_invalid_parameter(self):
        data = {
            'invalid': "None"
        }

        request: HttpRequest = self.factory.post("/sources/area_status", data)
        response = get_feed_status_for_area(request)

        print(response)

        self.assertEqual(response.status_code, 400)

