# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib import admin
from django.contrib.gis import admin
from .models import Subscription

class SubscriptionAdmin(admin.GISModelAdmin):
    list_display = ('id', 'last_heartbeat')

# Register your models here.
admin.site.register(Subscription, SubscriptionAdmin)
