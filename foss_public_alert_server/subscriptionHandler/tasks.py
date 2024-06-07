# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from celery import shared_task
from .models import Subscription
import datetime
from django.conf import settings


@shared_task(name="remove_old_subscriptions")
def remove_old_subscription():
    """
    deletes all subscription which hasn't sent a heartbeat since the in the settings defined number of days
    """
    for subscription in Subscription.objects:
        timedelta = datetime.datetime.now() - subscription.last_heartbeat
        if timedelta.days > settings.DAYS_INACTIVE_TIMEOUT:
            # @todo send last notification to client ?
            subscription.delete()
