import os
from django.conf import settings
from django.test import TestCase
# from .models import Alert
# Create your tests here.
from abstract_CAP_parser import AbstractCAPParser
import xml.etree.ElementTree as ET


class AlertHandlerCAPParserTestsCase(TestCase):

    @staticmethod
    def create_test_class_instance() -> AbstractCAPParser:
        return AbstractCAPParser("Test_source_id", "https://OnlyForTesting.de")

    @staticmethod
    def create_test_cap_data():
        return os.path.join(settings.BASE_DIR, '/alertHandler/test_data/test_cap_data_1.xml')

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