# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.conf import settings
from django.contrib import admin, messages
from .models import CAPFeedSource
from alertHandler.models import Alert

import glob
import os


class CAPSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_id', 'name')
    search_fields = ['source_id', 'cap_alert_feed']
    actions = ['purge_dangling_cap_files', 'reset_last_fetch_status']

    @admin.action(description="Purge dangling CAP files")
    def purge_dangling_cap_files(self, request, queryset):
        count = 0
        errors = 0
        for source in queryset:
            alert_files = []
            for alert in Alert.objects.filter(source_id=source.source_id):
                alert_files.append(alert.cap_data.path)

            to_delete = []
            for cap_file in glob.glob(f"{settings.MEDIA_ROOT}/alerts/{source.source_id}/*.xml"):
                if cap_file not in alert_files:
                    to_delete.append(cap_file)

            for file_name in to_delete:
                try:
                    os.remove(file_name)
                    count += 1
                except Exception as e:
                    print(f"Failed to delete {file_name} - {str(e)}")
                    errors += 1

        self.message_user(request, f"Removed {count} file(s), {errors} error(s)", messages.SUCCESS if errors == 0 else messages.ERROR)

    @admin.action(description="reset last fetch status")
    def reset_last_fetch_status(self, request, queryset):
        for source in queryset:
            print(source.id)

            CAPFeedSource.objects.filter(id=source.id).update(last_fetch_datetime=None)


    search_fields = ['source_id', 'cap_alert_feed']

admin.site.register(CAPFeedSource, CAPSourceAdmin)
