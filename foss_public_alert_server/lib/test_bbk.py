# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import unittest
import xml.etree.ElementTree as ET

from bbk import BBK


class TestBBK(unittest.TestCase):

    def test_to_cap(self):
        with open("testdata/mow.DE-HE-KS-SE106-20250313-106-001.json") as f:
            nina_json = json.load(f)

        cap_xml = BBK.json_to_cap(nina_json)

        ET.indent(cap_xml, space=' ', level=2)
        cap_str = ET.tostring(cap_xml, encoding='utf-8', xml_declaration=True)

        with open("testdata/mow.DE-HE-KS-SE106-20250313-106-001.xml", mode='rb', buffering=0) as f:
            ref_xml = f.readall()
        if cap_str != ref_xml:
            with open("testdata/mow.DE-HE-KS-SE106-20250313-106-001.xml.fail", mode='wb') as f:
                f.write(cap_str)
        self.assertEqual(cap_str, ref_xml)


if __name__ == '__main__':
    unittest.main()
