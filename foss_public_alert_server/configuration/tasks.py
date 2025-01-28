# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from celery import shared_task

from .models import AppSetting
from django.conf import settings

@shared_task(name="task.store_default_settings_in_database")
def add_default_settings():

    for setting in settings.DEFAULT_SETTINGS:
        match(setting[1]):
            case "char":
                setting = AppSetting(
                    setting_name=setting[0],
                    setting_type=setting[1],
                    char_value=setting[2]
                )
            case "int":
                setting = AppSetting(
                    setting_name=setting[0],
                    setting_type=setting[1],
                    int_value=setting[2]
                )
            case "float":
                setting = AppSetting(
                    setting_name=setting[0],
                    setting_type=setting[1],
                    float_value=setting[2]
                )
            case "bool":
                setting = AppSetting(
                    setting_name=setting[0],
                    setting_type=setting[1],
                    bool_value=setting[2]
                )
            case _:
                pass
                # todo add logger
        # store settings, if there is no database entry yet
        if not AppSetting.objects.filter(setting_name=setting.setting_name).exists():
            setting.save()


    """
       id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
       privacy_police =  models.CharField(max_length=255)
       imprint = models.CharField(max_length=255)
       operator = models.CharField(max_length=255)
       support_unifiedPush = models.BooleanField()
       support_unifiedPush_encrypted = models.BooleanField()
       support_apn = models.BooleanField()
       support_firebase = models.BooleanField()
       apn_provider_token = models.CharField(max_length=255)
       update_period_for_cap_feeds = models.CharField(max_length=255) # in sec
       day_inactive_timeout =  models.CharField(max_length=255)
       """