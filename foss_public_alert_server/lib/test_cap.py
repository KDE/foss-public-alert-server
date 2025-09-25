# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import unittest

import cap


class TestCAP(unittest.TestCase):

    def test_identifier(self):
        cap_msg = cap.CAPAlertMessage.from_file("../alertHandler/test_data/test_cap_data_1.xml")
        cap_id = cap_msg.identifier()
        self.assertEqual(cap_id, "urn:oid:1234.5678")

    def test_sent_time(self):
        cap_msg = cap.CAPAlertMessage.from_file("../alertHandler/test_data/test_cap_data_1.xml")
        sent_time = cap_msg.sent_time()
        self.assertEqual(sent_time, datetime.datetime.fromisoformat("2024-04-21T11:51:29-03:00"))

    def test_expire_time(self):
        cap_msg = cap.CAPAlertMessage.from_file("../alertHandler/test_data/test_cap_data_1.xml")
        expire_time = cap_msg.expire_time()
        self.assertFalse(cap_msg.is_expired())
        self.assertEqual(expire_time, datetime.datetime.fromisoformat("2199-04-22T10:00:00-03:00"))

    def test_is_expired(self):
        cap_msg = cap.CAPAlertMessage.from_file("../alertHandler/test_data/test_cap_data_expired_alert.xml")
        self.assertTrue(cap_msg.is_expired())

    def test_alert_info(self):
        cap_msg = cap.CAPAlertMessage.from_file("../alertHandler/test_data/test_cap_data_1.xml")
        cap_alert_infos = cap_msg.alert_infos()
        self.assertEqual(len(cap_alert_infos), 1)
        cap_alert_info = cap_alert_infos[0]
        self.assertEqual(cap_alert_info.event(), "TestCase")
        self.assertEqual(cap_alert_info.urgency(), "Future")
        self.assertEqual(cap_alert_info.severity(), "Moderate")
        self.assertEqual(cap_alert_info.language(), "de-DE")

    def test_scope(self):
        cap_msg = cap.CAPAlertMessage.from_file("../alertHandler/test_data/test_cap_data_1.xml")
        scope = cap_msg.scope()
        self.assertEqual(scope, "Public")

if __name__ == '__main__':
    unittest.main()
