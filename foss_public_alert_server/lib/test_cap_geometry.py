# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest

import cap
import cap_geometry


class TestCAP(unittest.TestCase):

    def test_antimeridian_polygon(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/gdacs-cap_1001150.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.valid)
        self.assertEqual(poly.geom_typeid, 6)  # multipolygon, consisting of two parts
        self.assertEqual(poly.num_geom, 2)

        if poly[0].envelope.extent[2] < 0:
            westExtent = poly[0].envelope.extent
            eastExtent = poly[1].envelope.extent
        else:
            westExtent = poly[1].envelope.extent
            eastExtent = poly[0].envelope.extent

        self.assertAlmostEqual(westExtent[1], -28.505)
        self.assertAlmostEqual(westExtent[3], -18.495)
        self.assertAlmostEqual(westExtent[0], -180)
        self.assertAlmostEqual(westExtent[2], -172.74234227419)

        self.assertAlmostEqual(eastExtent[1], -28.2242009)
        self.assertAlmostEqual(eastExtent[3], -15.365)
        self.assertAlmostEqual(eastExtent[0], 168.748971963339)
        self.assertAlmostEqual(eastExtent[2], 180)

    def test_antimeridian_polygon2(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/ru-20250301222516-0086037.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.valid)
        self.assertEqual(poly.geom_typeid, 6)
        self.assertGreaterEqual(poly.num_geom, 2)

        for p in poly:
            extent = p.envelope.extent
            self.assertGreater(extent[1], 61.5)
            self.assertLess(extent[3], 72.0)
            if extent[0] < 0:
                self.assertLess(extent[2], -169.5)
            else:
                self.assertGreater(extent[0], 157.7)

    def test_broken_selfintersection(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/gdacs-cap_1023542.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.valid)
        extent = poly.envelope.extent
        self.assertAlmostEqual(extent[1], 8.72977)
        self.assertAlmostEqual(extent[3], 8.83186)
        self.assertAlmostEqual(extent[0], -68.19886)
        self.assertAlmostEqual(extent[2], -68.06497)

    def test_near_self_intersection(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/noaa-2.49.0.1.840.0.bde6c30c43ead9c23c42bea7977652a7de76d87d.002.1.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.valid)
        extent = poly.envelope.extent
        self.assertAlmostEqual(extent[1], 38.1143)
        self.assertAlmostEqual(extent[3], 38.7042)
        self.assertAlmostEqual(extent[0], -76.337)
        self.assertAlmostEqual(extent[2], -75.7013)

    def test_parallel_lines(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/kz-2.49.0.0.398.0-20250306-133701-0284797-00-EN.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.valid)
        extent = poly.envelope.extent
        self.assertAlmostEqual(extent[1], 48.151)
        self.assertAlmostEqual(extent[3], 49.266)
        self.assertAlmostEqual(extent[0], 81.553)
        self.assertAlmostEqual(extent[2], 83.616)

    def test_slow_polygon(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/noaa-2.49.0.1.840.0.9b5195e635069329b12a7c697fad5934d144784a.001.1.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.valid)
        extent = poly.envelope.extent
        self.assertAlmostEqual(extent[1], 54.6645)
        self.assertAlmostEqual(extent[3], 57.0995)
        self.assertAlmostEqual(extent[0], -134.4221)
        self.assertAlmostEqual(extent[2], -130.0051)

    def test_empty_polygon_elemnts(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/il-488abaaf-cad5-4d2b-93b2-703016878453.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.empty)

    def test_tab_separated_coordinates(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/mo-cap_monsoon.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.valid)
        extent = poly.envelope.extent
        self.assertAlmostEqual(extent[1], 22.0766)
        self.assertAlmostEqual(extent[3], 22.217)
        self.assertAlmostEqual(extent[0], 113.5281)
        self.assertAlmostEqual(extent[2], 113.6301)

    def test_circle(self):
        polys = cap_geometry.polygon_from_cap_circle("23.8262083333333,120.185488888889 0.5")
        self.assertEqual(len(polys), 1)
        poly = polys[0]
        self.assertTrue(poly.valid)
        extent = poly.envelope.extent
        self.assertAlmostEqual(extent[0], 120.180, delta=0.001)
        self.assertAlmostEqual(extent[1], 23.821, delta=0.001)
        self.assertAlmostEqual(extent[2], 120.190, delta=0.001)
        self.assertAlmostEqual(extent[3], 23.830, delta=0.001)

    def test_circle_antimeridian_east(self):
        polys = cap_geometry.polygon_from_cap_circle("25.0,175.0 1000")
        self.assertEqual(len(polys), 2)

        polyEast = polys[0]
        self.assertTrue(polyEast.valid)
        extentEast = polyEast.envelope.extent
        self.assertAlmostEqual(extentEast[0], 165.07, delta=0.01)
        self.assertAlmostEqual(extentEast[1], 16.006, delta=0.01)
        self.assertAlmostEqual(extentEast[2], 180, delta=0.01)
        self.assertAlmostEqual(extentEast[3], 33.99, delta=0.01)

        polyWest = polys[1]
        self.assertTrue(polyWest.valid)
        extentWest = polyWest.envelope.extent
        self.assertAlmostEqual(extentWest[0], -180, delta=0.01)
        self.assertAlmostEqual(extentWest[1], 16.006, delta=0.01)
        self.assertAlmostEqual(extentWest[2], -175.07, delta=0.01)
        self.assertAlmostEqual(extentWest[3], 33.99, delta=0.01)

    def test_circle_antimeridian_west(self):
        polys = cap_geometry.polygon_from_cap_circle("-25.0,-175.0 1000")
        self.assertEqual(len(polys), 2)

        polyEast = polys[0]
        self.assertTrue(polyEast.valid)
        extentEast = polyEast.envelope.extent
        self.assertAlmostEqual(extentEast[0], 175.07, delta=0.01)
        self.assertAlmostEqual(extentEast[1], -33.99, delta=0.01)
        self.assertAlmostEqual(extentEast[2], 180, delta=0.01)
        self.assertAlmostEqual(extentEast[3], -16.006, delta=0.01)

        polyWest = polys[1]
        self.assertTrue(polyWest.valid)
        extentWest = polyWest.envelope.extent
        self.assertAlmostEqual(extentWest[0], -180, delta=0.01)
        self.assertAlmostEqual(extentWest[1], -33.99, delta=0.01)
        self.assertAlmostEqual(extentWest[2], -165.077, delta=0.01)
        self.assertAlmostEqual(extentWest[3], -16.006, delta=0.01)

    def test_polygon_antimeridian_split(self):
        cap_msg = cap.CAPAlertMessage.from_file("testdata/gdacs-cap_1470644.xml")
        poly = cap_geometry.multipolygon_from_cap_alert(cap_msg)
        self.assertTrue(poly.valid)
        self.assertAlmostEqual(poly.extent[0], -180)
        self.assertAlmostEqual(poly.extent[2], 180)


if __name__ == '__main__':
    unittest.main()
