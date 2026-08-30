# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from celery import shared_task
import logging

from .models import AppSetting
from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task(name="task.store_default_settings_in_database")
def add_default_settings():
    """
    Write the default settings to database
    This does not override existing settings.
    """
    app_setting = None
    for raw_setting in settings.DEFAULT_SETTINGS:
        match(raw_setting[1]):
            case "char":
                app_setting = AppSetting(
                    setting_name=raw_setting[0],
                    setting_type=raw_setting[1],
                    char_value=raw_setting[2]
                )
            case "int":
                app_setting = AppSetting(
                    setting_name=raw_setting[0],
                    setting_type=raw_setting[1],
                    int_value=raw_setting[2]
                )
            case "float":
                app_setting = AppSetting(
                    setting_name=raw_setting[0],
                    setting_type=raw_setting[1],
                    float_value=raw_setting[2]
                )
            case "bool":
                app_setting = AppSetting(
                    setting_name=raw_setting[0],
                    setting_type=raw_setting[1],
                    bool_value=raw_setting[2]
                )
            case _:
                logger.debug("No valid setting type found")
                continue
        # store settings, if there is no database entry yet
        if app_setting is not None:
            if not AppSetting.objects.filter(setting_name=raw_setting.setting_name).exists():
                app_setting.save()