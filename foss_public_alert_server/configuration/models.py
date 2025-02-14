# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from enum import Enum

class AppSetting(models.Model):
    class SettingsTypes(Enum):
        CHAR = ('char', 'CharField')
        BOOL = ('bool', 'BooleanField')
        INT = ('int', 'IntegerField')
        FLOAT = ('float', 'FloatField')

        @classmethod
        def to_list(cls):
            return list(map(lambda c: c.value, cls))

    setting_name = models.CharField(max_length=255, unique=True)
    setting_type = models.CharField(max_length=255, choices=SettingsTypes.to_list())
    char_value = models.CharField(max_length=255, blank=True, null=True)
    bool_value = models.BooleanField(blank=True, null=True)
    int_value = models.IntegerField(blank=True, null=True)
    float_value = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.setting_name

    def get_value(self):
        if self.setting_type == 'char':
            return self.char_value
        elif self.setting_type == 'bool':
            return self.bool_value
        elif self.setting_type == 'int':
            return self.int_value
        elif self.setting_type == 'float':
            return self.float_value
        return None

    @staticmethod
    def get(setting_name:str) -> str or bool or int or float or None:
        """
        get the settings entry with the key `setting_name`
        The result's datatype corresponds to the `setting_type`
        If `setting_name` is not defined, this method returns None
        :param setting_name: the key-value of the setting
        :return: the stored value for `setting_name`
        """
        try:
            return AppSetting.objects.get(setting_name=setting_name).get_value()
        except ObjectDoesNotExist:
            return None