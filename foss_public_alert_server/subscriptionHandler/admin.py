# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib import admin
from django.contrib.gis import admin
from .models import Subscription, ConnectionFlag

class SubscriptionAdmin(admin.GISModelAdmin):
    list_display = ['id', 'last_heartbeat']
    search_fields = ['id']

class ConnectionFlagAdmin(admin.GISModelAdmin):
    list_display = ['hostname']
    search_fields = ['hostname']

# Register your models here.
admin.site.register(Subscription, SubscriptionAdmin)

admin.site.register(ConnectionFlag, ConnectionFlagAdmin)

