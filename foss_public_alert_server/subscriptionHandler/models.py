# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib.gis.db import models

from datetime import datetime
import uuid


class Subscription(models.Model):
    class PushServices(models.IntegerChoices):
        UNIFIED_PUSH = 0, "UNIFIED_PUSH"
        UNIFIED_PUSH_ENCRYPTED = 1, "UNIFIED_PUSH_ENCRYPTED"
        APN = 2, "APN"
        FIREBASE = 3, "FIREBASE"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bounding_box = models.PolygonField()
    token = models.CharField(max_length=2048)
    push_service = models.IntegerField(choices=PushServices.choices, default=PushServices.UNIFIED_PUSH)
    last_heartbeat = models.DateTimeField(default=datetime.now)
    auth_key = models.CharField(max_length=255, null=True) # used by web push
    p256dh_key = models.CharField(max_length=255, null=True) # used by web push
    error_counter = models.IntegerField(default=0)
    error_messages = models.CharField(max_length=255, null=True)
    user_agent = models.CharField(max_length=255, null=True)
    vapid_public_key = models.CharField(max_length=96, null=True)  # only used by WebPush, so we have to allow null


class ConnectionFlag(models.Model):
    class FlagType(models.IntegerChoices):
        TIME_OUT = 0, "TIME_OUT"
        RATE_LIMIT = 1, "RATE_LIMIT"
    hostname = models.CharField(primary_key=True, max_length=255)
    set_time_stamp  = models.DateTimeField(default=datetime.now)
    expire_time_stamp = models.DateTimeField(default=datetime.now)
    type = models.IntegerField(choices=FlagType.choices, default=FlagType.TIME_OUT)
    error_message = models.CharField(max_length=255, null=True)
