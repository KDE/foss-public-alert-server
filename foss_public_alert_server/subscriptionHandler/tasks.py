# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import logging

from datetime import timezone, datetime
from celery import shared_task, Task

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

class NotificationBaseTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo) -> None:
        """The notification was unsuccessful.

        This handler will be executed after a task has failed. In our case, after all retries have failed.
        As we can not deliver any push notifications, we increase the error counter, and we delete the subscription
        when the error counter exceeds the max number defined in the settings to enforce a resubscribe from the client.
        :param exc: (Exception) - The exception raised by the task.
        :param task_id:
        :param args: (Tuple) - Original arguments for the task that failed.
        :param kwargs: (Dict) - Original keyword arguments for the task that failed.
        :param einfo:
        :return: None
        """
        # Only delete the subscriptions if we raised a PushNotificatioinException.
        # This avoids deleting subscriptions due to internal errors
        if isinstance(exc, PushNotificationException):
            subscription_id = args[0]

            # increase error counter by one
            logger.debug(f"Increase error counter of subscription {subscription_id}")
            subscription = Subscription.objects.get(id=subscription_id)
            subscription.error_counter += 1

            # delete subscription of error counter exceeds the max number
            if subscription.error_counter > AppSetting.get("NUMBER_OF_PUSH_ERRORS_BEFORE_DELETING"):
                logger.debug(f"Subscription {subscription_id} has reached the max error number. Deleting.")
                subscription.delete()
            else:
                subscription.save()

    def on_success(self, retval, task_id, args, kwargs) -> None:
        """The notification was successful.

         We can reset the error counter to 0 again.

        :param retval:
        :param task_id:
        :param args: Original arguments for the task that failed.
        :param kwargs: Original keyword arguments for the task that failed.
        :return: None
        """
        subscription_id = args[0]
        subscription = Subscription.objects.get(id=subscription_id)
        subscription.error_counter = 0
        subscription.save()

@shared_task(name="task.send_notification",
             bind=True,
             autoretry_for=(PushNotificationException,),
             retry_backoff=True,
             retry_backoff_max=1800, # 1800s = 30min
             retry_kwargs={'max_retries': 30 }, # results in 10h
             base=NotificationBaseTask)
def send_one_notification(self, subscription_id, msg)  -> None:
    """
    send one push notification.

    As these requests can fail, we use a retry policy with 12 tries and an exponential backoff.
    The last try wil be after ~34min
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
    except PushNotificationException as e:
        # reraise exception to make the task fail, to use the retry policy
        raise PushNotificationException


def check_for_alerts_and_send_notifications(alert: Alert, is_update: bool = False) -> None:
    """
    check for the given alert if there is a subscription that wants to get a notification
    :return: None
    """
    msg = {
        'type': 'added' if not is_update else 'update',
        'alert_id': str(alert.id)
        }
    for subscription in Subscription.objects.filter(bounding_box__intersects=alert.area):
        # send push notification task to celery to free the alert parsing worker
        send_one_notification.apply_async(
            args=[subscription.id, msg],
            # @TODO(Nucleus): we may want to use task routes instead of hardcoding the queue name here
            queue='push_notifications'
        )
        # @TODO(Nucleus): check performance
    pass
