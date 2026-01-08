# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import logging

from dateutil import parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CAPFeedEntry:
    """
    Methods for handling entries in CAP RSS feeds.
    """

    @staticmethod
    def expiry_time(entry) -> datetime.datetime:
        """
        Retrives and parses the expiry time from a feed entry.

        Returns a datetime value when parsing succeeded, None otherwise.
        """
        s = entry.get('cap_expires')
        return CAPFeedEntry.parse_date_time(s) if s is not None else None

    @staticmethod
    def parse_date_time(s: str) -> datetime.datetime:
        """
        Parses a CAP date/time string found in an CAP feed.

        This is supposed to be in ISO format, but in reality
        also other formats occur (such as those supported by RSS/Atom).
        """

        # we expect ISO time format, so try that first
        try:
            dt = parser.isoparse(s)
            if dt is not None:
                return dt
        except Exception:
            pass

        # otherwise try formats valid in RSS/Atom or otherwise observed
        formats = [
            "%a, %d %b %Y %H:%M:%S %z"
        ]
        for format in formats:
            try:
                dt = datetime.datetime.strptime(s, format)
                if dt is not None:
                    return dt
            except Exception:
                continue

        logger.info(f"Failed to parse CAP RSS datetime: {s}")
        return None
