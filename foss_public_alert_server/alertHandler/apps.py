# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.apps import AppConfig


class AlertHandlerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alertHandler'
