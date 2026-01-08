# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from dateutil import parser

import feedparser
import unittest

import cap_feed


class TestCAPFeed(unittest.TestCase):
    def test_parse_date_time(self):
        self.assertIsNone(cap_feed.CAPFeedEntry.parse_date_time(None))
        self.assertIsNone(cap_feed.CAPFeedEntry.parse_date_time("not a date"))
        self.assertEqual(cap_feed.CAPFeedEntry.parse_date_time("2026-01-01T06:30:17+00:00"), parser.isoparse("2026-01-01T06:30:17+00:00"))
        self.assertEqual(cap_feed.CAPFeedEntry.parse_date_time("Thu, 01 Jan 2026 06:40:13 +0200"), parser.isoparse("2026-01-01T06:40:13+02:00"))
        self.assertIsNone(cap_feed.CAPFeedEntry.parse_date_time("Don, 01 Jan 2026 06:40:13 +0200"))

    def test_expire_time(self):
        with open("testdata/au-bom-en.rss.xml", mode="rb", buffering=0) as f:
            feed = feedparser.parse(f.readall())
        self.assertFalse(feed.bozo)
        self.assertEqual(len(feed.entries), 1)
        entry = feed.entries[0]
        self.assertEqual(cap_feed.CAPFeedEntry.expiry_time(entry), parser.isoparse("2026-01-01T16:00:00Z"))


if __name__ == '__main__':
    unittest.main()
