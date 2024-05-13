import os
import xml
from abc import ABC, abstractmethod
import datetime
from django.contrib.gis.geos import Polygon
# import feedparser
import requests
import requests_cache
import requests
import xml.etree.ElementTree as ET
import json
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Alert


class AbstractCAPParser(ABC):
    feed_url = None
    session = None
    source = None
    parser = None

    def __init__(self, source_id, feed_url):
        self.feed_url = feed_url
        self.source = source_id
        self.session = requests_cache.session.CachedSession(cache_name='cache/' + self.source)

    @abstractmethod
    def get_feed(self):
        pass

    def find_identifier(self, cap_tree: xml) -> str:
        """
        find the identifier of the alert in the xml data and return it
        :param cap_tree: cap data of the alert
        :return: the identifier of the alert or an empty string in case of failure
        """

        # find identifier
        id_node = cap_tree.find('{urn:oasis:names:tc:emergency:cap:1.2}identifier')
        if id_node is None or not id_node.text:
            print(f"{self.source} - Couldn't find CAP alert message identifier, skipping")
            raise ValueError("Couldn't find CAP alert message identifier, skipping")
        return id_node.text

    def find_sent_time(self, cap_tree, alert_id) -> str:
        sent_time_node = cap_tree.find('{urn:oasis:names:tc:emergency:cap:1.2}sent')
        if sent_time_node is None or not sent_time_node.text:
            print(f"{self.source} - Couldn't find CAP alert message sent time, skipping {alert_id}")
            raise ValueError(f"{self.source} - Couldn't find CAP alert message sent time, skipping {alert_id}")
        return sent_time_node.text

    def find_expire_time(self, cap_tree, alert_id) -> datetime:
        expire_time: datetime = None

        for expireTimeNode in cap_tree.findall(
                '{urn:oasis:names:tc:emergency:cap:1.2}info/{urn:oasis:names:tc:emergency:cap:1.2}expires'):
            try:
                datatime = datetime.datetime.fromisoformat(expireTimeNode.text)
            except ValueError:
                continue
            if expire_time is None or datatime > expire_time:
                expire_time = datatime
            if expire_time is not None and expire_time < datetime.datetime.now(datetime.timezone.utc):
                print(f"{self.source} - skipping alert {alert_id} expired on {datatime}")
                raise ValueError(f"{self.source} - skipping alert {alert_id} expired on {datatime}")

        return expire_time

    @staticmethod
    def geojson_polygon_to_cap(coordinates):
        poly = ''
        for coord in coordinates[0]:
            poly += f"{coord[1]:.4f},{coord[0]:.4f} "
        return poly.strip()

    def expand_geocode(self, cap_tree: xml) -> [bool]:
        """
        Some sources do not include the polygons of the area direct in the CAP file but use geocodes instead.
        Therefore, we append the polygons as geojson to the file
        :param cap_tree: the original cap xml tree
        :return: true if the data is expanded false if not
        """
        expanded = False
        for area in cap_tree.findall('.//{urn:oasis:names:tc:emergency:cap:1.2}area'):
            # if they are already polygons, we do not have to expand the data
            if area.find('{urn:oasis:names:tc:emergency:cap:1.2}polygon'):
                continue
            for geocode in area.findall('{urn:oasis:names:tc:emergency:cap:1.2}geocode'):
                code_name = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}valueName').text
                code_value = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}value').text
                if not code_name or not code_value:
                    continue
                # find correct geojson file in storage
                # @todo think about better path
                code_file = os.path.join(settings.BASE_DIR, '/alertHandler/data', code_name, f"{code_value}.geojson")
                print("code file path is:" + str(code_file))
                if os.path.isfile(code_file):
                    geojson = json.load(open(code_file))
                    # append geojson to original file
                    if geojson['geometry']['type'] == 'Polygon':
                        poly = ET.SubElement(area, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
                        poly.text = self.geojson_polygon_to_cap(geojson['geometry']['coordinates'])
                        expanded = True
                    elif geojson['geometry']['type'] == 'MultiPolygon':
                        for coordinates in geojson['geometry']['coordinates']:
                            poly = ET.SubElement(area, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
                            poly.text = self.geojson_polygon_to_cap(coordinates)
                        expanded = True
                    else:
                        print(f"unhandled geometry type: {geojson['geometry']['type']}")
                else:
                    print(f"can't expand code {code_name}: {code_value}")
        return expanded

    def flatten_xml(self, node: xml) -> None:
        """
        remove whitespace at the beginning and ending from all text
        :param node: the root node of the xml tree
        :return: None
        """
        node.tail = None
        if node.text is not None:
            node.text = node.text.strip()
        for child in node:
            self.flatten_xml(child)


    @staticmethod
    def bbox_for_polygon(poly, min_lat, min_lon, max_lat, max_lon):
        if not poly:
            return min_lat, min_lon, max_lat, max_lon
        for point in poly.split(' '):
            coordinates = point.split(',')
            if len(coordinates) != 2:
                continue
            try:
                lat = float(coordinates[0])
                lon = float(coordinates[1])
            except ValueError:
                continue
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
        return min_lat, min_lon, max_lat, max_lon

    @staticmethod
    def bbox_for_circle(circle, min_lat, min_lon, max_lat, max_lon):
        (center, radius) = circle.split(' ')
        (lat, lon) = center.split(',')
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return min_lat, min_lon, max_lat, max_lon

        # TODO correct radius computation
        min_lat = min(min_lat, lat - 1.0)
        max_lat = max(max_lat, lat + 1.0)
        min_lon = min(min_lon, lon - 1.0)
        max_lon = max(max_lon, lon + 1.0)
        return min_lat, min_lon, max_lat, max_lon

    @staticmethod
    def is_valid_bounding_box(min_lon, min_lat, max_lon, max_lat):
        """
        validate if the given bounding box is valid and does not except valid values
        :param min_lon:
        :param min_lat:
        :param max_lon:
        :param max_lat:
        :return:
        """
        return (-180.0 <= min_lon <= 180.0
                and -180.0 <= min_lat <= 180.0
                and -90.0 <= max_lon <= 90.0
                and -90.0 <= max_lat <= 90.0
                and min_lon != min_lat
                and max_lon != max_lat)

    def determine_bounding_box(self, cap_tree: xml) -> (int, int, int, int):
        min_lat = 90
        min_lon = 180
        max_lat = -90
        max_lon = -180

        try:
            for polyNode in cap_tree.findall(
                    '{urn:oasis:names:tc:emergency:cap:1.2}info/{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}polygon'):
                (min_lat, min_lon, max_lat, max_lon) = self.bbox_for_polygon(polyNode.text, min_lat, min_lon, max_lat,
                                                                             max_lon)
            for circleNode in cap_tree.findall(
                    '{urn:oasis:names:tc:emergency:cap:1.2}info/{urn:oasis:names:tc:emergency:cap:1.2}area/{urn:oasis:names:tc:emergency:cap:1.2}circle'):
                (min_lat, min_lon, max_lat, max_lon) = self.bbox_for_circle(circleNode.text, min_lat, min_lon,
                                                                            max_lat, max_lon)

            if not self.is_valid_bounding_box(min_lon=min_lon, min_lat=min_lat, max_lat=max_lat, max_lon=max_lon):
                raise ValueError("bounding box is not valid")

            print(min_lat, min_lon, max_lat, max_lon)

        except Exception as e:
            print("Something went wrong while determining bounding box" + str(e))
        return min_lat, min_lon, max_lat, max_lon

    @staticmethod
    def write_to_database(new_alert: Alert):
        try:
            # @todo write to database maybe a problem with race conditions?
            print("Writing to database...")
            # check if alert is already in database
            alerts = Alert.objects.filter(source_id=new_alert.source_id, alert_id=new_alert.alert_id)
            if len(alerts) == 1:
                alert = alerts[0]
                # TODO look for changes and update/notify as needed
            else:
                print("bounding box is:")
                print(new_alert.bounding_box)
                new_alert.save()
            # print(new_alert)
        except Exception as e:
            print("Something went wrong while writing to database: " + str(e))

    def addAlert(self, cap_source_url: str = None, cap_data: xml = None):
        try:
            # print("Add new Alert")
            if not cap_data:
                print(f"{self.source} - Got no CAP alert message, skipping")
                return

            cap_data_modified: bool = False
            # crude way to normalize to CAP v1.2, US NWS still uses v1.1 data
            # @todo should not be necessary anymore it seams that they also use 1.2 now
            if 'urn:oasis:names:tc:emergency:cap:1.1' in cap_data:
                cap_data = cap_data.replace('urn:oasis:names:tc:emergency:cap:1.1',
                                            'urn:oasis:names:tc:emergency:cap:1.2')
                cap_data_modified = True

            ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
            try:
                cap_tree = ET.fromstring(cap_data)
            except ET.ParseError as e:
                print(f"{self.source} - failed to parse CAP alert message XML: {e}")
                print(cap_data)
                return

            # find identifier
            alert_id = self.find_identifier(cap_tree)

            # find sent time
            sent_time = self.find_sent_time(cap_tree, alert_id)

            # find expire time
            expire_time = self.find_expire_time(cap_tree, alert_id)

            # expand geocodes if necessary, and determine bounding box
            cap_data_modified |= self.expand_geocode(cap_tree)
            if cap_data_modified or cap_source_url is None:
                self.flatten_xml(cap_tree)
                cap_data = ET.tostring(cap_tree, encoding='utf-8', xml_declaration=True).decode()

            # determine bounding box and drop elements without
            (min_lat, min_lon, max_lat, max_lon) = self.determine_bounding_box(cap_tree)
            print(min_lat, min_lon, max_lat, max_lon)

            if min_lat > max_lat or min_lon > max_lon:
                print(f"{self.source} - No geographic data available for {alert_id} - skipping")
                return

            # to build a valid polygon. we have to fulfill the right-hand-rule
            # there we build the polygon with min_lon, min_lat, max_lon, max_lat
            bound_box_polygon = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))

            # self.alertIds.append(alertId) # @todo why?
            new_alert: Alert = Alert(
                source_id=self.source,
                alert_id=alert_id,
                bounding_box=bound_box_polygon,
                issue_time=sent_time,
            )

            if expire_time is not None:
                new_alert.expire_time = expire_time.isoformat()
            if cap_source_url:
                new_alert.source_url = cap_source_url
            if cap_data:
                # upload cap data file to the server
                new_alert.cap_data = SimpleUploadedFile(f"{alert_id}.xml", cap_data.encode('utf-8'),
                                                        'application/xml')
                new_alert.cap_data_modified = cap_data_modified

            # write alert to database
            self.write_to_database(new_alert)
        except Exception as e:
            print("Something went wrong while adding the new alert: " + str(e))
