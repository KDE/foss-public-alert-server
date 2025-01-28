# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib import admin
from .models import AppSetting

@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ('setting_name', 'setting_type', 'get_value')
    fields = ('setting_name', 'setting_type', 'char_value', 'bool_value', 'int_value', 'float_value')

