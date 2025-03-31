# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from celery import shared_task
from django.contrib.gis.geos import MultiPolygon, Polygon
from datetime import datetime, timedelta, timezone

from .models import TestAlert, CapFeed

@shared_task(name="task.create_test_alert")
def create_test_alert():
    # create a small polygon at the point Nemo
    point_nemo_lat = -48.8767
    point_nemo_lon = -123.3933
    offset = 1  # 1 degree offset for the square

    coordinates = [
        (point_nemo_lon - offset, point_nemo_lat - offset),  # Bottom-left
        (point_nemo_lon + offset, point_nemo_lat - offset),  # Bottom-right
        (point_nemo_lon + offset, point_nemo_lat + offset),  # Top-right
        (point_nemo_lon - offset, point_nemo_lat + offset),  # Top-left
        (point_nemo_lon - offset, point_nemo_lat - offset)  # Closing the polygon
    ]

    polygon = Polygon(coordinates)

    # get feed or create feed if not already exists
    feed_name = "XX-FPAS-EN"
    try:
        feed = CapFeed.objects.get(source_id=feed_name)
    except CapFeed.DoesNotExist:
        # create feed
        feed = CapFeed(source_id=feed_name)
        feed.save()

    new_alert: TestAlert = TestAlert(
        source_id=feed,
        alert_id=f"FPAS_{datetime.now(timezone.utc)}",
        sent=datetime.now(timezone.utc),
        sender= "FOSS Public Alert Sever",
        status=TestAlert.Status.Test,
        msg_type=TestAlert.MsgType.Alert,
        scope = TestAlert.Scope.Public,
        category = TestAlert.Category.Other,
        event="TEST ALERT",
        urgency = TestAlert.Urgency.Immediate,
        severity = TestAlert.Severity.Severe,
        certainty = TestAlert.Certainty.Observed,
        onset = datetime.now(timezone.utc),
        expires = datetime.now(timezone.utc)+timedelta(minutes=30),
        headline = "TEST Alert",
        description = "This is a test alert from the FOSS Public Alert Server. There is no real danger."
                      "You can safely ignore this alert.",
        areaDesc = "Point Nemo",
        polygon = MultiPolygon(polygon)
    )
    new_alert.save()
    print("Successfully saved test Alert")

@shared_task(name="task.delete_expired_test_alerts")
def delete_alert():
    """
    delete all expired test alerts
    :return:
    """
    all_alert = TestAlert.objects.all()
    for alert in all_alert:
        if alert.expires < datetime.now(timezone.utc):
            alert.delete()