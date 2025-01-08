# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import logging

from time import sleep
from celery import shared_task

from .XML_CAP_parser import XMLCAPParser
from .MOWAS_CAP_parser import MoWaSCapParser
from .DWD_CAP_parser import DWDCAPParser
from .models import Alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task()
def test_celery():
    for i in range(0, 11):
        print(i)
        sleep(1)
    return "Task complete!"


def check_if_alert_is_expired(expire_time:datetime) -> bool:
    """
    check if the expire_time is later than current time
    :param expire_time: the expire_time of the alert
    :return: true if alert is expired, false if not
    """
    return expire_time and expire_time < datetime.datetime.now(datetime.timezone.utc)


@shared_task(name="task.remove_expired_alerts")
def remove_expired_alerts() -> bool:
    """
    check for every alert if it is expired and delete every expired alert
    called by a periodic celery task
    :return:
    """
    for alert in Alert.objects.all():
        if check_if_alert_is_expired(alert.expire_time):
            logger.info(f"delete alert {alert.alert_id}")
            Alert.objects.filter(id=alert.id).delete()
            # the delete() sends also a signal to a class methode (Alert.auto_delete_capdata_on_delete)
            # to also delete the stored cap data
    return True
