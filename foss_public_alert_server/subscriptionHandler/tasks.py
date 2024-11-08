# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from celery import shared_task
from .models import Subscription

import json
import datetime
import requests

from celery import shared_task
from django.conf import settings

from alertHandler.models import Alert
from .models import Subscription


@shared_task(name="task.remove_old_subscriptions")
def remove_old_subscription():
    """
    deletes all subscription which hasn't sent a heartbeat since the in the settings defined number of days
    """
    for subscription in Subscription.objects.all():
        timedelta = datetime.datetime.now() - subscription.last_heartbeat
        if timedelta.days > settings.DAYS_INACTIVE_TIMEOUT:
            msg = "Subscription timed out and is deleted. please renew your subscription."
            requests.post(subscription.distributor_url, json.dumps(msg))
            subscription.delete()


def check_for_alerts_and_send_notifications(alert:Alert) -> None:
    """
    check for the given Alert if there is a subscription that wants to get a notification
    :return: None
    """
    print("check for push notifications")
    for subscription in Subscription.objects.filter(bounding_box__intersects=alert.bounding_box):
        print(f"Send notification for {subscription.id} to {subscription.distributor_url}")
        requests.post(subscription.distributor_url, json.dumps(alert.alert_id))
    # @todo check performance
    pass
