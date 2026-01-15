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
import logging
import socket

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from celery import shared_task


from .exceptions import AlertExpiredException, DatabaseWritingException, AlertParameterException, \
    NoGeographicDataAvailableException, NothingChangedException
from .models import Alert
from sourceFeedHandler.models import CAPFeedSource
from foss_public_alert_server.celery import app as celery_app
from subscriptionHandler.tasks import check_for_alerts_and_send_notifications
from lib import cap, cap_geojson, cap_geometry

# logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Disable extremely noisy GEOS warnings about self-intersecting polygons
if not settings.DEBUG:
    logging.getLogger('django.contrib.gis').setLevel(logging.ERROR)

# Reduce timeout for network operations to just 10 seconds
# If a feed or CAP message doesn't reply in that time it's likely dead anyway
# and potentially blocks other tasks for several minutes.
socket.setdefaulttimeout(10)


class AbstractCAPParser(ABC):
    feed_source: CAPFeedSource = None
    session = None
    parser = None
    name = None
    list_of_current_alert_ids = []

    def __init__(self, feed_source, name: str):
        self.feed_source = feed_source
        self.session = requests_cache.session.CachedSession(cache_name='cache/' + self.feed_source.source_id, expire_after=60*60*24)
        self.session.cache.delete(expired=True)
        self.session.cache.delete(invalid=True)
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
        store_warnings = True
        warnings_list = []
        self.list_of_current_alert_ids = []

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

            # update feed status information
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=True)
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(missing_geo_information=False)

            # process the warnings
            for warning in warnings_list:
                if str(warning).__contains__("no valid bounding box") or str(warning).__contains__("Unknown geometry code"):
                    # if there was min one invalid bounding box, set missing geo info to true
                    CAPFeedSource.objects.filter(id=self.feed_source.id).update(missing_geo_information=True)

            # delete all old alerts in the database
            for alert in Alert.objects.filter(source_id=self.feed_source.source_id):
                if alert.alert_id not in self.list_of_current_alert_ids:
                    logger.debug(f"{alert.alert_id} is no longer in the feed. Deleting...")
                    alert.delete()

        except NothingChangedException:
            logger.debug(f"{self.feed_source.source_id} - nothing changed")
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=True)
            # do not store empty warnings if we just checked for changes
            store_warnings = False
        except ET.ParseError as e:
            logger.exception(f"{self.feed_source.source_id} - failed to parse CAP alert message XML:", exc_info=e)
            warnings.warn(f"Failed to parse CAP alert message XML {e}")
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=False)
        except DatabaseWritingException as e:
            logger.exception(f"Something went wrong while writing in the database  "
                             f"{self.feed_source.source_id}", exc_info=e)
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=False)
            # do not add database exceptions to warnings because they could include sensitive information
            warnings_list.append("Database writing error")
        except Exception as e:
            logger.exception(f"Something went wrong while getting the feed {self.feed_source.source_id}", exc_info=e)
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_status=False)
            # add exceptions to warnings_lis
            warnings_list.append(str(e))

        if store_warnings:
            # store warnings in database
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(feed_warnings=str(warnings_list)[:255])

        # store duration as last fetch duration
        CAPFeedSource.objects.filter(id=self.feed_source.id).update(last_fetch_duration=datetime.now() - start_time)

    def load_geocode(self, code_name: str, code_value: str):
        """
        Load GeoJSON geometry for a given CAP geo code.
        Returns None if not found.
        """
        code_file = os.path.join(settings.BASE_DIR, 'alertHandler/data', code_name, f"{code_value}.geojson")
        if os.path.isfile(code_file):
            return json.load(open(code_file))

        # for hierarchical CPEAS codes check if we have a parent code at least
        if code_name == "CPEAS Geographic Code":
            for i in range(0, 3):
                parent_code = code_value[0:6 - i*2] + '0000000000'[4-i*2:]
                if parent_code != code_value:
                    return self.load_geocode(code_name, parent_code)

        return None

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
                geojson = self.load_geocode(code_name, code_value)
                if geojson is not None:
                    # append geojson to original file
                    expanded = cap_geojson.geojson_feature_to_cap(area, geojson) or expanded
                else:
                    if is_first_error_for_source:
                        is_first_error_for_source = False
                        warnings.warn(f"Unknown geometry code: {code_name}: {code_value}")
                        logger.error(
                            f"Geo error[{self.feed_source.source_id}] - can't expand code {code_name}: {code_value} "
                            f"(For all error messages see DEBUG level)")
                    else:
                        # this is not the first error for this source - hide the error at error level and just log
                        # at debug level to avoid spamming the logs
                        logger.debug(
                            f"Geo error[{self.feed_source.source_id}] - can't expand code {code_name}: {code_value}")

        return expanded

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
            # If the alert id is already in the database we got an update and need to notify accordingly.
            # The calling code ensures we don't get here for unchanged alerts.
            alerts = Alert.objects.filter(source_id=new_alert.source_id, alert_id=new_alert.alert_id)
            if len(alerts) == 1:
                new_alert.id = alerts[0].id
                old_path = alerts[0].cap_data.path
                new_alert.save(force_update=True)
                os.remove(old_path)
                check_for_alerts_and_send_notifications(new_alert, True)
            else:
                new_alert.save()
                # check if there are subscription
                check_for_alerts_and_send_notifications(new_alert)
        except Exception as e:
            raise DatabaseWritingException(str(e))

    def update_feed_source_entry(self, sent_time: datetime) -> None:
        """
        check if the sent_time is newer then the latest stored timestamps and if yes replace the old datetime with the new one
        :param sent_time: the sent time of the alert
        :return: None
        """
        latest_entry = CAPFeedSource.objects.filter(id=self.feed_source.id).first()
        if latest_entry is None or latest_entry.latest_published_alert_datetime is None:
            CAPFeedSource.objects.filter(id=self.feed_source.id).update(latest_published_alert_datetime=sent_time)
        elif sent_time > latest_entry.latest_published_alert_datetime:
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

            cap_msg = cap.CAPAlertMessage.from_string(cap_data)
            if cap_msg.is_expired():
                return
            if cap_msg.scope() == "Private":
                return

            # find identifier
            alert_id = cap_msg.identifier()

            # find sent time
            sent_time = cap_msg.sent_time()

            # if we already know the alert and it's sent time matches we assume nothing changed
            # if the sent time did change we got an update
            if len(Alert.objects.filter(source_id=self.feed_source.source_id, alert_id=alert_id, issue_time=sent_time)) == 1:
                self.record_unchanged_alert(alert_id)
                return

            # find expire time
            expire_time = cap_msg.expire_time()

            # expand geocodes if necessary
            cap_data_modified |= self.expand_geocode(cap_msg.xml)

            cap_data = cap_msg.to_string()

            polygon = cap_geometry.multipolygon_from_cap_alert(cap_msg)
            if polygon.empty or not polygon.valid:
                raise NoGeographicDataAvailableException(f"No geographic data available for {alert_id}")

            # validate if the source country of the alert is allowed to send alerts for this area
            # self.validate_if_alert_is_in_country_borders()

            # find an English alert info, otherwise take the first one
            # the resulting data is only used for the diagnostics map display, therefore
            # this sloppy multi-language handling is good enough here
            cap_info = None
            for info in cap_msg.alert_infos():
                if info.language().startswith("en"):
                    cap_info = info
                    break
            if cap_info is None:
                cap_info = cap_msg.alert_infos()[0]

            new_alert: Alert = Alert(
                source_id=self.feed_source.source_id,
                alert_id=alert_id,
                issue_time=sent_time,
                msg_type=cap_msg.msg_type(),
                status=cap_msg.status(),
                event=cap_info.event()[:255],
                severity=cap_info.severity(),
                urgency=cap_info.urgency(),
                area=polygon
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
            #warnings.warn(f"Unknown geometry code:[{self.feed_source.source_id}] - {str(e)} - skipping")
            logger.exception(f"Unknown geometry code:[{self.feed_source.source_id}]- skipping", exc_info=e)

    def record_unchanged_alert(self, alert_id: str):
        """
        Record a still active but unchanged alert as part of a fetch.
        Either addAlert or this have to be called to prevent alerts from
        being automatically rmeoved.
        """
        self.list_of_current_alert_ids.append(alert_id)
