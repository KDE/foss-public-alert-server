# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib.gis import admin
from .models import TestAlert, CapFeed

class TestAlertAdmin(admin.GISModelAdmin):
   list_display = ('source_id',)
   search_fields = ['source_id', 'alert_id']

admin.site.register([TestAlert, CapFeed], TestAlertAdmin)