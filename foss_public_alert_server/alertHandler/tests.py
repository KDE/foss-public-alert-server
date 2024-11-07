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
    def create_test_cap_data():
        f = open(os.path.join(settings.BASE_DIR, 'alertHandler/test_data/test_cap_data_1.xml'))
        return f.read()

    # test every helper methode
    def test_find_identifier(self):
        cap_data = self.create_test_cap_data()
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
