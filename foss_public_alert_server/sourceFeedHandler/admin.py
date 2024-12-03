# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib import admin
from .models import CAPFeedSource
# Register your models here.

class CAPSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_id', 'name')
    search_fields = ['source_id']

admin.site.register(CAPFeedSource, CAPSourceAdmin)