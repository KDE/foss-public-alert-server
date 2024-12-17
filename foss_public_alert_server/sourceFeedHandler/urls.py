# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import path

from . import views

urlpatterns = [
    path("status", views.generate_source_status_page, name="status_page"),
    path("area_status", views.get_feed_status_for_area, name="get_feed_status_for_area"),
    path("server_status", views.server_status, name="get_server_status"),
    path("", views.index)
]