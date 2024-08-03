import os
import xml
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
import datetime
import requests_cache
import json
import warnings

from django.contrib.gis.geos import Polygon
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from celery import shared_task
# from celery.contrib import rdb

from .Exceptions import AlertExpiredException, DatabaseWritingException, AlertParameterException, \
    NoGeographicDataAvailableException
from .models import Alert
from sourceFeedHandler.models import CAPFeedSource
from foss_public_alert_server.celery import app as celery_app
from subscriptionHandler.tasks import check_for_alerts_and_send_notifications


class AbstractCAPParser(ABC):
    feed_source: CAPFeedSource = None
    session = None
    parser = None
    name = None

    def __init__(self, feed_source, name: str):
        self.feed_source = feed_source
        self.session = requests_cache.session.CachedSession(cache_name='cache/' + self.feed_source.source_id)
        self.name = name

    @abstractmethod
    def _load_alerts_from_feed(self):
        """
        protected abstract methode to fetch and process the cap feed
        :return: None
        """
        pass

    @shared_task(name="get_feed")
    def get_feed(self) -> None:
        """
        get the feed and process the data
        :return: None
        """

        warnings_list = []

        # configure warnings to append every warning to our list of warnings
        def collect_warnings(message, category, filename, lineno, file=None, line=None):
            warnings_list.append(f"{category.__name__}: {message}")

        # write warning not to standard out but to our custom methode
        warnings.showwarning = collect_warnings

        try:
            # store the start time to measure the feeds update time
            start_time = datetime.datetime.now()
            # load and process the feed
            self._load_alerts_from_feed()
            # store the end time
            end_time = datetime.datetime.now()

            # store duration os last fetch
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_duration=end_time - start_time)

            # update feed status information
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=True)
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(missing_geo_information=False)

            # process the warnings
            for warning in warnings_list:
                print(warning)
                if str(warning).__contains__("no valid bounding box"):
                    # if there was min one invalid bounding box, set missing geo info to true
                    CAPFeedSource.objects.filter(id=self.feed_source.id).update(missing_geo_information=True)
        except Exception as e:
            print("Something went wrong while getting the Feed: " + str(e))
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=False)
            # add exceptions to warnings_lis
            warnings_list.append(str(e))
            # @todo add to error logger
        # store warnings in database
        CAPFeedSource.objects.filter(id=self.feed_source.id).update(feed_warnings=str(warnings_list))

    def find_identifier(self, cap_tree: xml) -> str:
        """
        find the identifier of the alert in the xml data and return it
        :param cap_tree: cap data of the alert
        :return: the identifier of the alert or an empty string in case of failure
        """
        id_node = cap_tree.find('{urn:oasis:names:tc:emergency:cap:1.2}identifier')
        if id_node is None or not id_node.text:
            print(f"{self.feed_source.source_id} - Couldn't find CAP alert message identifier, skipping")
            raise AlertParameterException("Couldn't find CAP alert message identifier, skipping")
        return id_node.text

    def find_sent_time(self, cap_tree, alert_id) -> str:
        """
        find the sent time of the alert in the xml data and return it
        :param cap_tree: cap data of the alert
        :param alert_id: the identifier of the alert
        :return: the sent time of the alert
        :raise: valueError if it can not find the sent time
        """
        sent_time_node = cap_tree.find('{urn:oasis:names:tc:emergency:cap:1.2}sent')
        if sent_time_node is None or not sent_time_node.text:
            print(f"{self.feed_source.source_id} - Couldn't find CAP alert message sent time, skipping {alert_id}")
            raise AlertParameterException(
                f"{self.feed_source.source_id} - Couldn't find CAP alert message sent time, skipping {alert_id}")
        return sent_time_node.text

    @staticmethod
    def find_expire_time(cap_tree, alert_id) -> datetime:
        """
        find the expiry time in the CAP data and return it
        :param cap_tree: cap data of the alert
        :param alert_id: the identifier of the alert
        :return: the expiry time of the alert or None we if it could not find one
        :raise: ValueError if the alert is already expired
        """
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
                # print(f"{self.feed_source.source_id} - skipping alert {alert_id} expired on {datatime}")
                raise AlertExpiredException(f"alert {alert_id} expired on {datatime}")
        return expire_time

    @staticmethod
    def geojson_polygon_to_cap(coordinates) -> str:
        """
        Converts a polygon to cap data
        :param coordinates:
        :return: a string with the coordinates
        """
        poly: str = ''
        for coord in coordinates[0]:
            poly += f"{coord[1]:.4f},{coord[0]:.4f} "
        return poly.strip()

    def expand_geocode(self, cap_tree: xml) -> [bool]:
        """
        Some sources do not contain the polygons of the area directly in the CAP file, but use geocodes instead.
        If necessary, we add the polygons to the file as geojson.
        :param cap_tree: the original cap xml tree
        :return: true if the data is expanded false if not
        """
        expanded: bool = False
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
                # @todo think about better path?
                code_file = os.path.join(settings.BASE_DIR, 'alertHandler/data', code_name, f"{code_value}.geojson")
                # print("code file path is:" + str(code_file))
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
                    # if code_name == "EMMA_ID" or code_name == "FIPS" or code_name == "NUTS2" or code_name == "NUTS3":
                    #    rdb.set_trace()  # set breakpoint
        return expanded

    def flatten_xml(self, node: xml) -> None:
        """
        remove whitespace at the beginning and end of the entire text in the xml-tree
        :param node: the root node of the xml tree
        :return: None
        """
        node.tail = None
        if node.text is not None:
            node.text = node.text.strip()
        for child in node:
            self.flatten_xml(child)

    @staticmethod
    def bbox_for_polygon(poly, min_lat, min_lon, max_lat, max_lon) -> tuple[int, int, int, int]:
        """
        creates a bounding box from the given polygon.
        Uses the min_lat, min_lon as lower bound and max_lat, max_lon as upper bound. Only updates the
        values if the polygon exceeds these values
        :param poly: the polygon
        :param min_lat: the current minimal latitude
        :param min_lon: the current minimal longitude
        :param max_lat: the current maximal latitude
        :param max_lon: the current maximal longitude
        :return: new values of min_lat, min_lon, max_lat, max_lon if the polygon had lower/higher
        values or the previous values if not
        """
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
        """
        creates a bounding box from the given circle.
        Uses the min_lat, min_lon as lower bound and max_lat, max_lon as upper bound. Only updates the
        values if the circle exceeds these values
        :param poly: the polygon
        :param min_lat: the current minimal latitude
        :param min_lon: the current minimal longitude
        :param max_lat: the current maximal latitude
        :param max_lon: the current maximal longitude
        :return: new values of min_lat, min_lon, max_lat, max_lon if the polygon had lower/higher
        values or the previous values if not
        """
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
    def is_valid_bounding_box(min_lon, min_lat, max_lon, max_lat) -> bool:
        """
        validate if the given bounding box is valid and does not except valid values.
        :param min_lon: the minimal longitude of the bounding box
        :param min_lat: the minimal latitude of the bounding box
        :param max_lon: the maximal longitude of the bounding box
        :param max_lat: the maximal latitude of the bounding box
        :return: true if the bounding box if valid, false if not
        """
        return (-180.0 <= min_lon <= 180.0
                and -180.0 <= min_lat <= 180.0
                and -90.0 <= max_lon <= 90.0
                and -90.0 <= max_lat <= 90.0
                and min_lon != min_lat
                and max_lon != max_lat)

    def determine_bounding_box(self, cap_tree: xml, alert_id) -> (int, int, int, int):
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
                # @todo for dwd we do nto get an valid bounding box
                raise AlertParameterException(f"alert {alert_id} has no valid bounding box: {min_lat}, {min_lon}, "
                                              f"{max_lat}, {max_lon}")

            # print(min_lat, min_lon, max_lat, max_lon)

        except Exception as e:
            raise e
        return min_lat, min_lon, max_lat, max_lon

    def validate_if_alert_is_in_country_borders(self) -> bool:
        """
        check if the B-box is inside the allowed area of the country
        The check shouldn't be necessary and is just to avoid faulty or malicious alerts
        :return: True if the alert is in the allowed area, False if not
        """
        country_code = self.feed_source.authorityCountry
        # @todo implement
        return True

    @staticmethod
    def write_to_database_and_send_notification(new_alert: Alert) -> None:
        """
        write the given alert to the database and check if we have to sent notifications
        only stores the alert in the database if the alert is not already stored in the database
        :param new_alert: the alert to store in the database
        :return: None
        """
        try:
            # print("Writing to database...")
            # check if alert is already in database
            alerts = Alert.objects.filter(source_id=new_alert.source_id, alert_id=new_alert.alert_id)
            if len(alerts) == 1:
                alert = alerts[0]
                # TODO look for changes and update/notify if needed
            else:
                new_alert.save()
                # check if there are subscription
                check_for_alerts_and_send_notifications(new_alert)
        except Exception as e:
            raise DatabaseWritingException(str(e))

    def addAlert(self, cap_source_url: str = None, cap_data: xml = None) -> None:
        """
        parse the alert and store it in the database
        :param cap_source_url: the url of the cap source
        :param cap_data: the xml data of the cap alert
        :return: None
        :warns: if the alert can not be parsed correctly we raise a warning
        """
        try:
            # print("Add new Alert")
            if not cap_data:
                print(f"{self.feed_source.source_id} - Got no CAP alert message, skipping")
                return

            cap_data_modified: bool = False
            # crude way to normalize to CAP v1.2, US NWS still uses v1.1 data
            # @todo should not be necessary anymore it seems that they also use 1.2 now
            if 'urn:oasis:names:tc:emergency:cap:1.1' in cap_data:
                cap_data = cap_data.replace('urn:oasis:names:tc:emergency:cap:1.1',
                                            'urn:oasis:names:tc:emergency:cap:1.2')
                cap_data_modified = True

            ET.register_namespace('', 'urn:oasis:names:tc:emergency:cap:1.2')
            try:
                cap_tree = ET.fromstring(cap_data)
            except ET.ParseError as e:
                print(f"{self.feed_source.source_id} - failed to parse CAP alert message XML: {e}")
                print(cap_data)
                return

            # find identifier
            alert_id = self.find_identifier(cap_tree)

            # find sent time
            sent_time = self.find_sent_time(cap_tree, alert_id)

            # find expire time
            expire_time = self.find_expire_time(cap_tree, alert_id)

            # expand geocodes if necessary
            cap_data_modified |= self.expand_geocode(cap_tree)

            self.flatten_xml(cap_tree)
            cap_data = ET.tostring(cap_tree, encoding='utf-8', xml_declaration=True).decode()

            # determine bounding box and drop elements without
            (min_lat, min_lon, max_lat, max_lon) = self.determine_bounding_box(cap_tree, alert_id)
            # print(min_lat, min_lon, max_lat, max_lon)

            # validate if the source country of the alert is allowed to send alerts for this area
            # self.validate_if_alert_is_in_country_borders()

            if min_lat > max_lat or min_lon > max_lon:
                raise NoGeographicDataAvailableException(f"{self.feed_source.source_id}"
                       f" - No geographic data available for {alert_id} - skipping")

            # to build a valid polygon. we have to fulfill the right-hand-rule
            # there we build the polygon with min_lon, min_lat, max_lon, max_lat
            bound_box_polygon = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))

            # self.alertIds.append(alertId) # @todo why?
            new_alert: Alert = Alert(
                source_id=self.feed_source.source_id,
                alert_id=alert_id,
                bounding_box=bound_box_polygon,
                issue_time=sent_time,
            )

            if expire_time is not None:
                new_alert.expire_time = expire_time.isoformat()
            if cap_source_url:
                new_alert.source_url = cap_source_url
            if cap_data:
                # set the cap_data field to a simple file representation. The filepath is determined in the model
                new_alert.cap_data = SimpleUploadedFile(f"{alert_id}.xml", cap_data.encode('utf-8'),
                                                        'application/xml')
                new_alert.cap_data_modified = cap_data_modified

            # write alert to database
            self.write_to_database_and_send_notification(new_alert)
        except DatabaseWritingException as e:
            warnings.warn(f"Database error: {str(e)} - skipping")
        except AlertExpiredException as e:
            # nothing to do if an alert is expired
            # warnings.warn(f"Alert Expired: [{self.feed_source.source_id}] - {str(e)} - skipping")
            pass
        except AlertParameterException as e:
            warnings.warn(f"Parameter error:[{self.feed_source.source_id}] - {str(e)} - skipping")
