# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from celery import shared_task
from .models import Subscription

import json
from datetime import timezone, datetime
import requests
import logging

from celery import shared_task
from django.conf import settings

from alertHandler.models import Alert
from .models import Subscription
from configuration.models import AppSetting
from subscriptionHandler.push_notification_services import unified_push, unified_push_encrpted, apn, firebase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task(name="task.remove_old_subscriptions")
def remove_old_subscription():
    """
    deletes all subscription which hasn't sent a heartbeat since the in the settings defined number of days
    """
    for subscription in Subscription.objects.all():
        timedelta = datetime.now(timezone.utc) - subscription.last_heartbeat
        if timedelta.days > AppSetting.get("DAYS_INACTIVE_TIMEOUT"):
            msg = "Subscription timed out and is deleted. please renew your subscription."
            requests.post(subscription.distributor_url, json.dumps(msg))
            subscription.delete()


def check_for_alerts_and_send_notifications(alert:Alert) -> None:
    """
    check for the given Alert if there is a subscription that wants to get a notification
    :return: None
    """
    logger.info("check for push notifications")
    for subscription in Subscription.objects.filter(bounding_box__intersects=alert.bounding_box):
        # @todo is the distributor_url to sensitive to write it into logs?
        logger.debug(f"Send notification for {subscription.id} to {subscription.token}")
        match subscription.push_service:
            case "UnifiedPush":
                unified_push.send_notification(subscription.token, json.dumps(alert.alert_id))
            case "UnifiedPush_encrypted":
                unified_push_encrpted.send_notification(subscription.token,json.dumps(alert.alert_id), None)
            case "APN":
                apn.send_notification(subscription.token, "", "", "", "", "")
            case "Firebase":
                firebase.send_notification(subscription.token, json.dumps(alert.alert_id))

            # @todo check performance
    pass
