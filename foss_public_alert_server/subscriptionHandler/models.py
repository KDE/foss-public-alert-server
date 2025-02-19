# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import models
from django.dispatch import receiver
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
    token = models.CharField(max_length=255) # @todo 255 enough?
    push_service = models.IntegerField(choices=PushServices.choices, default=PushServices.UNIFIED_PUSH)
    last_heartbeat = models.DateTimeField(default=datetime.now)
