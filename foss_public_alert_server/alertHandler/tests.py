# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import logging
from datetime import datetime, timezone
from django.conf import settings
from django.test import TestCase
from sourceFeedHandler.models import CAPFeedSource

from .exceptions import AlertExpiredException
from .models import Alert
from .abstract_CAP_parser import AbstractCAPParser
from .XML_CAP_parser import XMLCAPParser
import xml.etree.ElementTree as ET

from lib import cap_geojson

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertHandlerCAPParserTestsCase(TestCase):

    @staticmethod
    def create_test_class_instance() -> AbstractCAPParser:
        feed = CAPFeedSource(
            id="fffec57e-6679-4b29-bb42-a49c11a91678",
            source_id="Test_source_id",
            feedSource="https://OnlyForTesting.de"
        )
        return XMLCAPParser(feed)

    @staticmethod
    def create_test_cap_data(filename: str):
        f = open(os.path.join(settings.BASE_DIR, f'alertHandler/test_data/{filename}'))
        return f.read()

    def create_test_xml_tree(self, cap_data) -> (AbstractCAPParser, ET.XML):
        abstract_cap_parser = self.create_test_class_instance()

        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
        try:
            cap_tree = ET.fromstring(cap_data)
        except ET.ParseError as e:
            logger.debug(f"failed to parse CAP alert message XML: {e}")
            logger.debug(cap_data)
            return

        return abstract_cap_parser, cap_tree

    # test every helper methode
    def test_expand_geocode_polygon_exists(self):
        cap_data = self.create_test_cap_data('test_cap_data_1.xml')
        abstract_cap_parser = self.create_test_class_instance()
        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')

        try:
            cap_tree = ET.fromstring(cap_data)
        except ET.ParseError as e:
            logger.debug(f"failed to parse CAP alert message XML: {e}")
            logger.debug(cap_data)
            return

        before_polygon = cap_tree.find(
            '{urn:oasis:names:tc:emergency:cap:1.2}info/{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}polygon')
        expand_geocode = abstract_cap_parser.expand_geocode(cap_tree)
        after_polygon = cap_tree.find(
            '{urn:oasis:names:tc:emergency:cap:1.2}info/{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}polygon')

        self.assertEqual(before_polygon, after_polygon)
        self.assertEqual(expand_geocode, False)

    def test_expand_geocode_without_polygon(self):
        cap_data = self.create_test_cap_data('test_cap_data_without_polygon_EMMA_ID_AT001.xml')
        abstract_cap_parser = self.create_test_class_instance()
        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')

        try:
            cap_tree = ET.fromstring(cap_data)
        except ET.ParseError as e:
            logger.debug(f"failed to parse CAP alert message XML: {e}")
            logger.debug(cap_data)
            return

        expand_geocode: ET.XML = abstract_cap_parser.expand_geocode(cap_tree)
        added_polygon: ET.XML() = cap_tree.find(
            '{urn:oasis:names:tc:emergency:cap:1.2}info/{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}polygon')
        expected_polygon_raw = {"geometry": {"coordinates": [[
            [16.2452, 47.4371], [16.311, 47.4842], [16.3305, 47.505], [16.3622, 47.6078], [16.3676, 47.6397],
            [16.3532, 47.6679], [16.3079, 47.7047], [16.2841, 47.7856], [16.2921, 47.8164], [16.434, 47.9178],
            [16.4604, 47.9324], [16.6807, 47.9997], [16.7154, 48.0099], [17.0036, 48.0872], [17.049, 48.1016],
            [17.036, 48.1369], [16.9796, 48.2089], [16.9529, 48.2464], [16.927, 48.2703], [16.8554, 48.3422],
            [16.8495, 48.3989], [16.8571, 48.4517], [16.9276, 48.5028], [16.946, 48.5275], [16.9453, 48.6256],
            [16.8846, 48.6951], [16.8633, 48.7159], [16.6758, 48.7804], [16.6483, 48.7885], [15.5157, 48.9153],
            [15.17, 48.9619], [14.7016, 48.6247], [14.6695, 48.5952], [14.7017, 48.5806], [14.8084, 48.5493],
            [14.873, 48.5265], [14.9086, 48.5042], [14.9765, 48.2931], [14.9554, 48.2156], [14.929, 48.2027],
            [14.7034, 48.1616], [14.6598, 48.1656], [14.6583, 48.12], [14.7312, 47.7871], [14.7281, 47.7494],
            [14.753, 47.7357], [14.7792, 47.7268], [14.8658, 47.7139], [14.9234, 47.7106], [14.9534, 47.7142],
            [15.1345, 47.7454], [15.2079, 47.7633], [15.274, 47.7846], [15.4148, 47.7826], [15.4539, 47.7755],
            [15.5755, 47.7482], [15.7062, 47.6995], [15.7319, 47.6877], [16.0613, 47.5237], [16.0925, 47.5048],
            [16.1563, 47.4344], [16.1664, 47.4088], [16.2452, 47.4371]
        ]], "crs": {"properties": {"name": "EPSG:4326"}, "type": "name"},
            "type": "Polygon"},
            "properties": {"code": "AT001", "country": "AT", "name": "Nieder\u00f6sterreich",
                           "type": "EMMA_ID"}, "type": "Feature"}
        expected_polygon = cap_geojson.geojson_polygon_to_cap(expected_polygon_raw['geometry']['coordinates'])

        self.assertEqual(expand_geocode, True)
        self.assertEqual(added_polygon.text, expected_polygon)

    def test_update_feed_source_entry(self):
        cap_data = self.create_test_cap_data('test_cap_data_1.xml')
        abstract_cap_parser, cap_tree = self.create_test_xml_tree(cap_data)

        CAPFeedSource.objects.create(id="fffec57e-6679-4b29-bb42-a49c11a91678", source_id="Test_source_id", feedSource="https://OnlyForTesting.de")

        # test with new sent_time if the time is correctly updated
        sent_time_1 = "2024-04-21T11:51:29-03:00"
        sent_time_datetime_1 = datetime.fromisoformat(sent_time_1)
        abstract_cap_parser.update_feed_source_entry(sent_time_1)
        self.assertEqual(CAPFeedSource.objects.count(), 1)
        db_entry: CAPFeedSource = CAPFeedSource.objects.first()
        self.assertEqual(db_entry.latest_published_alert_datetime, sent_time_datetime_1,
                         f"sent_time was not updated. Expected {sent_time_1} but"
                         f" was {db_entry.latest_published_alert_datetime}")

        # test for with older sent_time and expect no change
        sent_time_2 = datetime.fromisoformat("2023-04-21T11:51:29-03:00")
        abstract_cap_parser.update_feed_source_entry(sent_time_2)
        self.assertEqual(CAPFeedSource.objects.count(), 1)
        db_entry: CAPFeedSource = CAPFeedSource.objects.first()
        self.assertEqual(db_entry.latest_published_alert_datetime, sent_time_datetime_1,
                         f"sent_time should not be updated. Expected {sent_time_1} but"
                         f" was {db_entry.latest_published_alert_datetime}")

    def test_addAlert(self):
        cap_data = self.create_test_cap_data('test_cap_data_1.xml')
        abstract_cap_parser, cap_tree = self.create_test_xml_tree(cap_data)

        abstract_cap_parser.addAlert(cap_data=cap_data, cap_source_url="https://OnlyForTesting.de")

        self.assertEqual(Alert.objects.count(), 1)

        alert = Alert.objects.first()

        self.assertEqual(alert.alert_id, "urn:oid:1234.5678")
        self.assertEqual(alert.expire_time, datetime.fromisoformat("2199-04-22T10:00:00-03:00"))
        self.assertEqual(alert.issue_time, datetime.fromisoformat("2024-04-21T11:51:29-03:00"))
        bbox = alert.area.envelope.extent
        self.assertEqual(bbox[0], 6.328)
        self.assertEqual(bbox[1], 49.182)
        self.assertEqual(bbox[2], 13.931)
        self.assertEqual(bbox[3], 52.843)
        self.assertEqual(alert.source_url, "https://OnlyForTesting.de")
        self.assertEqual(alert.cap_data_modified, False)

    def test_addAlert_invalid_parameters(self):
        cap_data = self.create_test_cap_data('test_cap_data_1.xml')
        abstract_cap_parser, cap_tree = self.create_test_xml_tree(cap_data)

        abstract_cap_parser.addAlert()
        self.assertEqual(Alert.objects.count(), 0)
