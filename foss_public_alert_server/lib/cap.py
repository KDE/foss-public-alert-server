# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import re
import xml.etree.ElementTree as ET

from dateutil import parser
from datetime import datetime, timezone


class CAPException(BaseException):
    """
    Raised for violation of the CAP specification.
    """
    pass


class CAPPolygon:
    """
    Methods for parsing CAP polygon data.
    """

    @staticmethod
    def parse_polygon(cap_polygon: str):
        """
        Parses the given CAP polygon string and returns a list of (lon, lat) tuples.

        Applies a number of fixes for common errors (open polygons, garbage in the polygon string).
        Returns None if no valid polygon could be parsed.
        """
        coords = []
        for cap_coord in re.split(r'\s', cap_polygon):
            # remove garbage found in e.g. GDACS CAP files
            cap_coord = cap_coord.translate(str.maketrans('', '', '()'))
            cap_point = cap_coord.split(',')
            if len(cap_point) != 2:
                continue
            try:
                coord = (float(cap_point[1]), float(cap_point[0]))
            except Exception:
                continue
            coords.append(coord)

        if len(coords) < 4:
            return None

        # ensure polygon is closed
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        return coords


class CAPAlertInfo:
    """
    Represents a CAP alert info element in a CAP alert message XML tree.
    """

    xml = None

    def __init__(self, xml):
        self.xml = xml

    def event(self) -> str:
        return self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}event').text

    def expire_time(self) -> datetime:
        """
        Returny the expiry time of this CAP alert info.
        """
        node = self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}expires')
        if node is None or not node.text:
            return None

        try:
            time = parser.isoparse(node.text)
        except ValueError:
            return None
        return time

    def is_expired(self) -> bool:
        """
        Returns whether this CAP alert info is expired.
        """
        time = self.expire_time()
        return True if time is not None and time < datetime.now(timezone.utc) else False

    def language(self) -> str:
        """
        The language of this alert info element.
        """
        elem = self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}language')
        return elem.text if elem is not None else 'en-US'

    def severity(self) -> str:
        return self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}severity').text

    def urgency(self) -> str:
        return self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}urgency').text

    def polygons(self):
        """
        Returns a list of CAP polygon strings of the affected area of this alert.
        """
        polys = []
        for poly_node in self.xml.findall('{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}polygon'):
            if poly_node.text:
                polys.append(poly_node.text)
        return polys

    def circles(self):
        """
        Retursn a list of CAP circle strings of the affected area of this alert.
        """
        circles = []
        for circle_node in self.xml.findall('{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}circle'):
            circles.append(circle_node.text)
        return circles


class CAPAlertMessage:
    """
    Represents a CAP alert message.
    """

    xml = None

    def alert_infos(self):
        infos = []
        for info in self.xml.findall('{urn:oasis:names:tc:emergency:cap:1.2}info'):
            infos.append(CAPAlertInfo(info))
        return infos

    def expire_time(self) -> datetime:
        """
        Returns the latest expiry time of all CAP alert info elements.
        """
        time = None
        for info in self.alert_infos():
            t = info.expire_time()
            if t is None:
                continue
            time = t if time is None else max(time, t)
        return time

    def identifier(self) -> str:
        """
        Returns the CAP message identifier.
        Raises an exception if there is none.
        """
        id_node = self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}identifier')
        if id_node is None or not id_node.text:
            raise CAPException("Couldn't find CAP alert message identifier")
        return id_node.text

    def is_expired(self) -> bool:
        """
        Returns whether all CAP alert info elements in this CAP alert are expired.
        """
        return all(info.is_expired() for info in self.alert_infos())

    def msg_type(self) -> str:
        return self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}msgType').text

    def sent_time(self) -> datetime:
        """
        Returns the sent time of this CAP alert message.
        Raises an excpetion when not present or not parsable as datetime.
        """
        sent_time_node = self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}sent')
        if sent_time_node is None or not sent_time_node.text:
            raise CAPException("Couldn't find CAP alert message sent time.")
        return parser.isoparse(sent_time_node.text)

    def status(self):
        return self.xml.find('{urn:oasis:names:tc:emergency:cap:1.2}status').text

    def polygons(self):
        """
        Returns a list of CAP polygons of the affected areas of the alert infos of this CAP message.
        Duplicates are removed.
        """
        polys = set()
        for cap_info in self.alert_infos():
            polys |= set(cap_info.polygons())
        return list(polys)

    def circles(self):
        """
        Returns a list of CAP circles of the affected areas of the alert infos of this CAP message.
        Duplicates are removed.
        """
        circles = set()
        for cap_info in self.alert_infos():
            circles |= set(cap_info.circles())
        return list(circles)

    @staticmethod
    def from_string(cap_data: str):
        """
        Returns a CAPAlertMessage object for the given CAP XML string
        """
        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
        msg = CAPAlertMessage()
        msg.xml = ET.fromstring(cap_data)
        return msg

    @staticmethod
    def from_file(file_name):
        """
        Loads a CAP message from the given file name.
        """
        ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
        msg = CAPAlertMessage()
        msg.xml = ET.parse(file_name).getroot()
        return msg

    def __flatten_xml(self, node: xml) -> None:
        """
        Internal, removes whitespace at the beginning and end of the entire text in the xml-tree.
        """
        node.tail = None
        if node.text is not None:
            node.text = node.text.strip()
        for child in node:
            self.__flatten_xml(child)

    def to_string(self) -> str:
        """
        Serializes this CAP message to an XML string
        """
        self.__flatten_xml(self.xml)
        return ET.tostring(self.xml, encoding='utf-8', xml_declaration=True).decode()
