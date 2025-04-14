# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import os
import unittest

import cap
import cap_geojson


class TestCAPGeoJson(unittest.TestCase):
    def test_geojson_polygon_to_cap(self):
        coordinate_raw = {"geometry": {"coordinates": [
            [[15.548333151546686, 48.91076750142937], [15.575068458831433, 48.905356266254856],
             [15.820682797527303, 48.875127253584324], [16.038111270345468, 48.85303086511381],
             [16.847072835710364, 48.39893923921197], [16.853133779614105, 48.341154686565595]]]},
        }
        expected_coordinates = ("48.9108,15.5483 48.9054,15.5751 "
                                "48.8751,15.8207 48.8530,16.0381 "
                                "48.3989,16.8471 48.3412,16.8531")
        cap_polygon = cap_geojson.geojson_polygon_to_cap(coordinate_raw['geometry']['coordinates'])
        self.assertEqual(cap_polygon, expected_coordinates)

    def test_geojson_feature_to_cap(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/ie-2.49.0.1.372.0.250413231648.N_Norm002_SmallCraft.xml")
        for area in cap_msg.xml.findall('.//{urn:oasis:names:tc:emergency:cap:1.2}area'):
            for geocode in area.findall('{urn:oasis:names:tc:emergency:cap:1.2}geocode'):
                code_name = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}valueName').text
                code_value = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}value').text
                code_file = os.path.join('../alertHandler/data', code_name, f"{code_value}.geojson")
                self.assertTrue(os.path.isfile(code_file))
                with open(code_file) as f:
                    geojson = json.load(f)
                self.assertTrue(cap_geojson.geojson_feature_to_cap(area, geojson))
        self.assertEqual(len(cap_msg.xml.findall('.//{urn:oasis:names:tc:emergency:cap:1.2}polygon')), 4)


if __name__ == '__main__':
    unittest.main()
