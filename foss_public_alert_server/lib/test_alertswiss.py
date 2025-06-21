# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import unittest
import xml.etree.ElementTree as ET

from alertswiss import AlertSwiss
from cap import CAPAlertMessage


class TestAlertSwiss(unittest.TestCase):

    def test_to_cap(self):
        test_files = ["POA-1216107687-4", "POA-1222963954-5", "TEST-1163"]

        for test_file in test_files:
            with open(f"testdata/alertswiss-{test_file}.json") as f:
                swiss_json = json.load(f)

            msg = CAPAlertMessage()
            msg.xml = AlertSwiss.json_to_cap_message(swiss_json)
            msg.xml.append(AlertSwiss.json_to_cap_info(swiss_json, "en"))

            ET.indent(msg.xml, space=' ', level=2)
            cap_str = ET.tostring(msg.xml, encoding='utf-8', xml_declaration=True)

            with open(f"testdata/alertswiss-{test_file}.xml", mode='rb', buffering=0) as f:
                ref_xml = f.readall()
            if cap_str != ref_xml:
                with open(f"testdata/alertswiss-{test_file}.xml.fail", mode='wb') as f:
                    f.write(cap_str)
            self.assertEqual(cap_str, ref_xml)


if __name__ == '__main__':
    unittest.main()
