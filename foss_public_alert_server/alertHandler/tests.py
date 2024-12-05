# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from django.conf import settings
from django.test import TestCase
from sourceFeedHandler.models import CAPFeedSource
from .abstract_CAP_parser import AbstractCAPParser
from .XML_CAP_parser import XMLCAPParser
import xml.etree.ElementTree as ET

class AlertHandlerCAPParserTestsCase(TestCase):

    @staticmethod
    def create_test_class_instance() -> AbstractCAPParser:
        feed = CAPFeedSource(
            source_id="Test_source_id",
            feedSource="https://OnlyForTesting.de"
        )
        return XMLCAPParser(feed)

    @staticmethod
    def create_test_cap_data(testFile):
        f = open(os.path.join(settings.BASE_DIR, 'alertHandler/test_data', testFile))
        return f.read()

    # test every helper methode
    def test_find_identifier(self):
        cap_data = self.create_test_cap_data('test_cap_data_1.xml')
        abstract_cap_parser = self.create_test_class_instance()

        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
        try:
            cap_tree = ET.fromstring(cap_data)
        except ET.ParseError as e:
            print(f"failed to parse CAP alert message XML: {e}")
            print(cap_data)
            return

        cap_id = abstract_cap_parser.find_identifier(cap_tree)
        self.assertEquals(cap_id, "urn:oid:1234.5678")

    # test circle bounding box computation
    def test_circle_area(self):
        cap_data = self.create_test_cap_data('circle-area.xml')
        abstract_cap_parser = self.create_test_class_instance()

        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
        try:
            cap_tree = ET.fromstring(cap_data)
        except ET.ParseError as e:
            print(f"failed to parse CAP alert message XML: {e}")
            return

        (min_lat, min_lon, max_lat, max_lon) = abstract_cap_parser.determine_bounding_box(cap_tree, 'dummy')
        self.assertTrue(AbstractCAPParser.is_valid_bounding_box(min_lon=min_lon, min_lat=min_lat, max_lat=max_lat, max_lon=max_lon))
