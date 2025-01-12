# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import xml
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import requests_cache
import json
import warnings
import math
import logging

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

# logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbstractCAPParser(ABC):
    feed_source: CAPFeedSource = None
    session = None
    parser = None
    name = None
    list_of_current_alert_ids = []

    def __init__(self, feed_source, name: str):
        self.feed_source = feed_source
        self.session = requests_cache.session.CachedSession(cache_name='cache/' + self.feed_source.source_id, expire_after=60*60*24)
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

        # configure warnings (aka error messages) to append every warning to our list of warnings
        def collect_warnings(message, category, filename, lineno, file=None, line=None):
            warnings_list.append(f"{category.__name__}: {message}")

        # write warning not to standard out but to our custom methode
        warnings.showwarning = collect_warnings

        try:
            # store the start time to measure the feeds update time
            start_time = datetime.now()
            # load and process the feed
            self._load_alerts_from_feed()
            # store the end time
            end_time = datetime.now()

            # store duration os last fetch
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_duration=end_time - start_time)

            # update feed status information
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=True)
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(missing_geo_information=False)

            # process the warnings
            for warning in warnings_list:
                if str(warning).__contains__("no valid bounding box"):
                    # if there was min one invalid bounding box, set missing geo info to true
                    CAPFeedSource.objects.filter(id=self.feed_source.id).update(missing_geo_information=True)

            # delete all old alerts in the database
            for alert in Alert.objects.filter(source_id=self.feed_source.source_id):
                if alert.alert_id not in self.list_of_current_alert_ids:
                    logger.info(f"{alert.alert_id} is no longer in the feed. Deleting...")
                    alert.delete()

        except Exception as e:
            logger.exception(f"Something went wrong while getting the feed {self.feed_source.source_id}", exc_info=e)
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=False)
            # add exceptions to warnings_lis
            warnings_list.append(str(e))
        # store warnings in database
        CAPFeedSource.objects.filter(id=self.feed_source.id).update(feed_warnings=str(warnings_list)[:255])

    def find_identifier(self, cap_tree: xml) -> str:
        """
        find the identifier of the alert in the xml data and return it
        :param cap_tree: cap data of the alert
        :return: the identifier of the alert or an empty string in case of failure
        """
        id_node = cap_tree.find('{urn:oasis:names:tc:emergency:cap:1.2}identifier')
        if id_node is None or not id_node.text:
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
                datatime = datetime.fromisoformat(expireTimeNode.text)
            except ValueError:
                continue
            if expire_time is None or datatime > expire_time:
                expire_time = datatime
            if expire_time is not None and expire_time < datetime.now(timezone.utc):
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

    def geojson_feature_to_cap(self, area, geojson) -> bool:
        """
        Add a GeoJSON polygon from a GEoJSON feature to the CAP <area> element.
        :param area: the CAP <area> element to add the geometry to
        :param geojson: A GeoJSON feature object
        :return: True if a viable polygon was found and could be added, False otherwise
        """
        if geojson['geometry']['type'] == 'Polygon':
            poly = ET.SubElement(area, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
            poly.text = self.geojson_polygon_to_cap(geojson['geometry']['coordinates'])
            return True
        elif geojson['geometry']['type'] == 'MultiPolygon':
            for coordinates in geojson['geometry']['coordinates']:
                poly = ET.SubElement(area, '{urn:oasis:names:tc:emergency:cap:1.2}polygon')
                poly.text = self.geojson_polygon_to_cap(coordinates)
            return True
        else:
            logger.warning(f"{self.feed_source.source_id} - unhandled geometry type: {geojson['geometry']['type']}")
            return False


    def expand_geocode(self, cap_tree: xml) -> [bool]:
        """
        Some sources do not contain the polygons of the area directly in the CAP file, but use geocodes instead.
        If necessary, we add the polygons to the file as geojson.
        :param cap_tree: the original cap xml tree
        :return: true if the data is expanded false if not
        """
        expanded: bool = False
        is_first_error_for_source = True
        for area in cap_tree.findall('.//{urn:oasis:names:tc:emergency:cap:1.2}area'):
            # if they are already polygons, we do not have to expand the data
            if (area.find('{urn:oasis:names:tc:emergency:cap:1.2}polygon') is not None
                    or area.find('{urn:oasis:names:tc:emergency:cap:1.2}circle') is not None):
                continue
            for geocode in area.findall('{urn:oasis:names:tc:emergency:cap:1.2}geocode'):
                code_name = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}valueName').text
                code_value = geocode.find('{urn:oasis:names:tc:emergency:cap:1.2}value').text
                if not code_name or not code_value:
                    continue
                # find correct geojson file in storage
                # @todo think about better path?
                code_file = os.path.join(settings.BASE_DIR, 'alertHandler/data', code_name, f"{code_value}.geojson")
                if os.path.isfile(code_file):
                    geojson = json.load(open(code_file))
                    # append geojson to original file
                    expanded = expanded or self.geojson_feature_to_cap(area, geojson)
                else:
                    if is_first_error_for_source:
                        is_first_error_for_source = False
                        logger.error(
                            f"Geo error[{self.feed_source.source_id}] - can't expand code {code_name}: {code_value} "
                            f"(For all error messages see DEBUG level)")
                    else:
                        # this is not the first error for this source - hide the error at error level and just log
                        # at debug level to avoid spamming the logs
                        logger.debug(
                            f"Geo error[{self.feed_source.source_id}] - can't expand code {code_name}: {code_value}")

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
    def distance(lat1, lon1, lat2, lon2):
        """
        Compoutes the distance in meters between two geographic coordinates.
        """
        earth_radius = 6371000.0; # in meters
        d_lat = math.radians(lat1 - lat2)
        d_lon = math.radians(lon1 - lon2)
        a = math.pow(math.sin(d_lat / 2.0), 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.pow(math.sin(d_lon / 2.0), 2)
        return 2.0 * earth_radius * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

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
            radius = float(radius) * 1000.0 # CAP specifies radius in kilometer, we need meter below
        except ValueError:
            return min_lat, min_lon, max_lat, max_lon

        dlon = radius / AbstractCAPParser.distance(lat, 0.0, lat, 1.0)
        dlat = radius / AbstractCAPParser.distance(0.0, lon, 1.0, lon)
        min_lat = min(min_lat, lat - dlat)
        max_lat = max(max_lat, lat + dlat)
        min_lon = min(min_lon, lon - dlon)
        max_lon = max(max_lon, lon + dlon)
        return min_lat, min_lon, max_lat, max_lon

    @staticmethod
    def is_valid_bounding_box(min_lon, min_lat, max_lon, max_lat) -> bool:
        """
        validate if the given bounding box is valid and does not except valid values.
        :param min_lon: the minimal longitude of the bounding box (-180 - +180)
        :param min_lat: the minimal latitude of the bounding box (-90 - +90)
        :param max_lon: the maximal longitude of the bounding box (-180 - +180)
        :param max_lat: the maximal latitude of the bounding box (-90 - +90)
        :return: true if the bounding box if valid, false if not
        """
        polygon:Polygon = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))
        # I'm not sure what exactly this check tests, maybe it's not necessary
        is_valid =  polygon.valid
        is_in_lat_lon_range = (-180 <= min_lon <= 180 and
                               -180 <=max_lon <= 180 and
                               -90 <= min_lat <= 90 and
                               -90 <= max_lat <= 90 and
                                min_lon != min_lat and
                               max_lon != max_lat)

        if not is_valid or not is_in_lat_lon_range:
            logger.debug(f"BBox is invalid because of: {polygon.valid_reason}")
        return is_valid and is_in_lat_lon_range

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
                raise AlertParameterException(f"{self.feed_source.source_id} - alert {alert_id} has no valid bounding box: {min_lat}, {min_lon}, "
                                              f"{max_lat}, {max_lon}")


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

    def update_feed_source_entry(self, sent_time:str) -> None:
        """
        check if the sent_time is newer then the latest stored timestamps and if yes replace the old datetime with the new one
        :param sent_time: the sent time of the alert
        :return: None
        """
        sent_time_datetime:datetime = datetime.fromisoformat(sent_time)
        latest_entry = CAPFeedSource.objects.filter(id=self.feed_source.id).first()
        if latest_entry is None or latest_entry.latest_published_alert_datetime is None:
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(latest_published_alert_datetime=sent_time)
        elif sent_time_datetime > latest_entry.latest_published_alert_datetime:
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(latest_published_alert_datetime=sent_time)

    def addAlert(self, cap_source_url: str = None, cap_data: xml = None) -> None:
        """
        parse the alert and store it in the database
        :param cap_source_url: the url of the cap source
        :param cap_data: the xml data of the cap alert
        :return: None
        :warns: if the alert can not be parsed correctly we raise a warning
        """
        try:
            if not cap_data:
                logger.info(f"{self.feed_source.source_id} - Got no CAP alert message, skipping")
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
                logger.exception(f"{self.feed_source.source_id} - failed to parse CAP alert message XML:", exc_info=e)
                logger.debug(cap_data)
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

            self.update_feed_source_entry(sent_time)

            # add alert to temp list. this allows us to delete all alerts which are not in the feed anymore
            self.list_of_current_alert_ids.append(new_alert.alert_id)
            # write alert to database
            self.write_to_database_and_send_notification(new_alert)
        except DatabaseWritingException as e:
            warnings.warn(f"Database error: {str(e)} - skipping")
            logger.exception(f"Database error: {str(e)} - skipping")
        except AlertExpiredException as e:
            # nothing to do if an alert is expired
            # warnings.warn(f"Alert Expired: [{self.feed_source.source_id}] - {str(e)} - skipping")
            pass
        except AlertParameterException as e:
            warnings.warn(f"Parameter error:[{self.feed_source.source_id}] - {str(e)} - skipping")
            logger.exception(f"Parameter error:[{self.feed_source.source_id}] skipping", exc_info=e)
        except NoGeographicDataAvailableException as e:
            warnings.warn(f"Unknown geometry code:[{self.feed_source.source_id}] - {str(e)} - skipping")
            logger.exception(f"Unknown geometry code:[{self.feed_source.source_id}]- skipping", exc_info=e)
