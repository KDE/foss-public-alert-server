# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import models
from django.dispatch import receiver
from django.contrib.gis.db import models

from datetime import datetime
import os
import uuid


# Create your models here.

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bounding_box = models.PolygonField()
    distributor_url = models.CharField(max_length=255)
    last_heartbeat = models.DateTimeField(default=datetime.now)

