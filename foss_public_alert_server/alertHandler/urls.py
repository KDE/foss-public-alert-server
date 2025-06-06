# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import path

from . import views

urlpatterns = [
    path("<uuid:identifier>", views.get_alert_cap_data),
    path("all", views.get_alerts_for_subscription_id, name="get_all_alerts"),
    path("area", views.get_alerts_for_area, name="get_alerts_for_area"),
    path("map", views.alert_map),
]
