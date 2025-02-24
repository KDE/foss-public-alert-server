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
    def test_geojson_polygon_to_cap(self):
        cap_data = self.create_test_cap_data('test_cap_data_1.xml')
        abstract_cap_parser, cap_tree = self.create_test_xml_tree(cap_data)
        coordinate_raw = {"geometry": {"coordinates": [
            [[15.548333151546686, 48.91076750142937], [15.575068458831433, 48.905356266254856],
             [15.820682797527303, 48.875127253584324], [16.038111270345468, 48.85303086511381],
             [16.847072835710364, 48.39893923921197], [16.853133779614105, 48.341154686565595]]]},
        }
        expected_coordinates = ("48.9108,15.5483 48.9054,15.5751 "
                                "48.8751,15.8207 48.8530,16.0381 "
                                "48.3989,16.8471 48.3412,16.8531")
        cap_polygon = abstract_cap_parser.geojson_polygon_to_cap(coordinate_raw['geometry']['coordinates'])
        self.assertEqual(cap_polygon, expected_coordinates)

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
        expected_polygon_raw = {"geometry": {"coordinates": [
            [[15.548333151546686, 48.91076750142937], [15.575068458831433, 48.905356266254856],
             [15.820682797527303, 48.875127253584324], [16.038111270345468, 48.85303086511381],
             [16.454225401646916, 48.80994218026878], [16.647723929583954, 48.786172967178025],
             [16.675036114032693, 48.77817008135829], [16.862005633301443, 48.71380251348272],
             [16.882589767856164, 48.69370885308812], [16.91964898610454, 48.64626080021502],
             [16.942900829589195, 48.624054236719665], [16.94356489743498, 48.52829074474883],
             [16.92588102675021, 48.5045628389069], [16.854850789212335, 48.45307490893995],
             [16.847072835710364, 48.39893923921197], [16.853133779614105, 48.341154686565595],
             [16.92538431284092, 48.268628760454284], [16.951102387451918, 48.2447934433506],
             [16.97772802105657, 48.207468509992935], [17.03390441746881, 48.135691585173284],
             [17.045925037256367, 48.10311829562693], [17.002917556815333, 48.089493864925075],
             [16.7147965355304, 48.01216555016799], [16.68006465018319, 48.00198263624809],
             [16.459499252137277, 47.93459196454559], [16.43291908444437, 47.91990313057937],
             [16.358156596735896, 47.87077365656082], [16.28992635002149, 47.81752509030166],
             [16.281671599381028, 47.78560148733771], [16.30577696574491, 47.703287589691335],
             [16.35133512997662, 47.66635292520849], [16.36508406492787, 47.63929029536625],
             [16.359920947648284, 47.60834343853959], [16.328356793005838, 47.506191266817034],
             [16.30938417788972, 47.486001894271084], [16.244069461157373, 47.439273419231284],
             [16.16779063573297, 47.41180539406996], [16.15840030938402, 47.435629159469244],
             [16.117397718994916, 47.482064904732795], [16.0939367383115, 47.50674560089238],
             [16.062422060771638, 47.525774643696366], [15.732945762603022, 47.689819148849],
             [15.707171407563257, 47.701688676482576], [15.6103589372103, 47.73897099144493],
             [15.576002282267432, 47.750553546504264], [15.454363939351978, 47.77779000813724],
             [15.415165655944383, 47.78493328193212], [15.309942196028365, 47.78914177556588],
             [15.273174312664393, 47.78681717959319], [15.206959916018548, 47.765509490588784],
             [15.168056511328842, 47.75410992818825], [15.134340904141913, 47.74781367660886],
             [14.953075638723234, 47.71660145757701], [14.923283966919504, 47.71299295839835],
             [14.866042207849702, 47.71625108944242], [14.779721001670417, 47.729081860328364],
             [14.753997248086037, 47.73786686850972], [14.730593665632874, 47.750771792914804],
             [14.733623613444719, 47.787387243402236], [14.722993878907515, 47.831061231156795],
             [14.696105376937481, 47.95533771598171], [14.660660793905043, 48.12017750813539],
             [14.662125054545157, 48.16303031289236], [14.703508910446224, 48.1591613487314],
             [14.9297699473478, 48.200433987371824], [14.957058848984504, 48.2137165113852],
             [14.971757812429232, 48.25762910896241], [14.9788330436416, 48.29357425444545],
             [14.910619451976714, 48.50579067942282], [14.874036360575714, 48.52862398239875],
             [14.809152752866694, 48.55152966200541], [14.702567063319096, 48.58283826142891],
             [14.673807642657884, 48.595846630623086], [14.703088166221342, 48.62281716579655],
             [14.924119155128052, 48.78281171068258], [15.170573660046834, 48.959397606917925],
             [15.515672169149127, 48.9129247505981], [15.548333151546686, 48.91076750142937]],
            [[16.383208146473024, 48.126828726238706], [16.413107636056964, 48.12823070031696],
             [16.44590433072004, 48.13238007480088], [16.487398989891844, 48.14478393599406],
             [16.53222021199223, 48.16757705643749], [16.544896550668398, 48.20328193135584],
             [16.54805753402595, 48.2389585786234], [16.538043600495733, 48.26678242518259],
             [16.513676175679578, 48.28120199256601], [16.485758773411604, 48.28971676972021],
             [16.446652283771535, 48.284054246828205], [16.27520741713422, 48.26986747659327],
             [16.234705295193482, 48.265021239460886], [16.198283816272948, 48.255477288098604],
             [16.186233896057445, 48.223877324219245], [16.188483618747266, 48.164377352095116],
             [16.212935188146105, 48.14077783585809], [16.239459000801656, 48.13055270659479],
             [16.270634970060627, 48.12607998903181], [16.30529542207659, 48.1235924587773],
             [16.383208146473024, 48.126828726238706]]], "crs": {"properties": {"name": "EPSG:4326"}, "type": "name"},
            "type": "Polygon"},
            "properties": {"code": "AT001", "country": "AT", "name": "Nieder\u00f6sterreich",
                           "type": "EMMA_ID"}, "type": "Feature"}
        expected_polygon = abstract_cap_parser.geojson_polygon_to_cap(expected_polygon_raw['geometry']['coordinates'])

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
        bbox = alert.bounding_box.envelope.extent
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
