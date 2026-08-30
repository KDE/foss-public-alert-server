# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
import logging

from time import sleep
from celery import shared_task

from .XML_CAP_parser import XMLCAPParser
from .DWD_CAP_parser import DWDCAPParser
from .models import Alert

logger = logging.getLogger("app")

@shared_task()
def test_celery():
    for i in range(0, 11):
        print(i)
        sleep(1)
    return "Task complete!"


@shared_task(name="task.remove_expired_alerts")
def remove_expired_alerts() -> bool:
    """
    check for every alert if it is expired and delete every expired alert
    called by a periodic celery task
    :return:
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    Alert.objects.filter(expire_time__lt=now).delete()
    return True
