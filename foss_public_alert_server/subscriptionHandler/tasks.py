# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
from datetime import timezone, datetime
import logging

from celery import shared_task

from alertHandler.models import Alert
from requests import ReadTimeout, RequestException, HTTPError, ConnectionError

from .exceptions import PushNotificationException
from .models import Subscription
from configuration.models import AppSetting
from .push_notification_services import unified_push, apn, firebase, unified_push_encrpted

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task(name="task.remove_old_subscriptions")
def remove_old_subscription():
    """
    deletes all subscription which hasn't sent a heartbeat since the in the settings defined number of days
    or have a push error counter above the defined limit
    """
    msg = {'type': 'unsubscribe',
           'message': "Your subscription timed out and has been deleted."
                      " Please renew your subscription."}

    for subscription in Subscription.objects.all():
        timedelta = datetime.now(timezone.utc) - subscription.last_heartbeat
        #  check if the error counter reached the limit
        if subscription.error_counter > AppSetting.get("NUMBER_OF_PUSH_ERRORS_BEFORE_DELETING"):
            # as we have a broken push config for this subscription, there is no reason to send a last notification to it
            subscription.delete()
            continue
        # @TODO(Nucleus): We should move this to a celery task with a retry policy and only delete the subscription after all tries failed or if the subscription was successfully sent.
        # check if the subscription is expired
        if timedelta.days > AppSetting.get("DAYS_INACTIVE_TIMEOUT"):
            try:
                match subscription.push_service:
                    case subscription.PushServices.UNIFIED_PUSH:
                        unified_push.send_notification(subscription.token, json.dumps(msg))
                    case subscription.PushServices.UNIFIED_PUSH_ENCRYPTED:
                        unified_push_encrpted.send_notification(subscription.token,
                                                                json.dumps(msg),
                                                                auth_key=subscription.auth_key,
                                                                p256dh_key=subscription.p256dh_key)
                    case subscription.PushServices.APN:
                        apn.send_notification(subscription.token, "", "", "", "", "")
                    case subscription.PushServices.FIREBASE:
                        firebase.send_notification(subscription.token, json.dumps(msg))
            except (PushNotificationException, ConnectionError, HTTPError, ReadTimeout, RequestException):
                 pass
            subscription.delete()


@shared_task(name="task.send_notification",
             bind=True,
             autoretry_for=(PushNotificationException,),
             retry_backoff=True,
             retry_kwargs={'max_retries': 12})
def send_one_notification(self, subscription_id, msg)  -> None:
    """
    send one push notification.

    As these requests can fail, we use a retry policy with 12 tries and an exponential backoff.
    The last try wil be after ~34min
    With every failed try, we increase the error counter. This error counter gets reset if we successfully send a push notification
    :param self:
    :param subscription_id: the id of the subscription
    :param msg: the payload to send via the push notification
    :return: None
    :raise PushNotificationException: in case the push notification couldn't deliver
    """
    subscription = Subscription.objects.get(id=subscription_id)
    logger.debug("Sending push notification")
    try:
        match subscription.push_service:
            case subscription.PushServices.UNIFIED_PUSH:
                unified_push.send_notification(subscription.token, json.dumps(msg))
            case subscription.PushServices.UNIFIED_PUSH_ENCRYPTED:
                unified_push_encrpted.send_notification(subscription.token,
                                                        json.dumps(msg),
                                                        auth_key=subscription.auth_key,
                                                        p256dh_key=subscription.p256dh_key)
            case subscription.PushServices.APN:
                apn.send_notification(subscription.token, "", "", "", "", "")
            case subscription.PushServices.FIREBASE:
                firebase.send_notification(subscription.token, json.dumps(msg))

        # we successfully delivered a push notification, reset the error counter and clear the error messages
        subscription.error_counter = 0
        subscription.error_messages = ""
        subscription.save()
    except PushNotificationException as e:
        # increase error counter and store error message in database
        subscription.error_counter = subscription.error_counter +1
        subscription.error_messages = e
        subscription.save()
        # reraise exception to make the task fail, to use the retry policy
        raise PushNotificationException

def check_for_alerts_and_send_notifications(alert:Alert) -> None:
    """
    check for the given alert if there is a subscription that wants to get a notification
    :return: None
    """
    msg = {
        'type': 'added',
        'alert_id': str(alert.id)
        }
    for subscription in Subscription.objects.filter(bounding_box__intersects=alert.bounding_box):
        # send push notification task to celery to free the alert parsing worker
        send_one_notification.apply_async(
            args=[subscription.id, msg],
            # @TODO(Nucleus): we may want to use task routes instead of hardcoding the queue name here
            queue='push_notifications'
        )
        # @TODO(Nucleus): check performance
    pass
