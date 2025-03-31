# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib import admin
from .models import Alert
from django.contrib.gis import admin

# Register your models here.

class AlertAdmin(admin.GISModelAdmin):
    list_display = ('id', 'source_id', 'alert_id', 'issue_time', 'expire_time')
    search_fields = ['id', 'source_id', 'alert_id']

admin.site.register(Alert, AlertAdmin)

