# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import path

from . import views

urlpatterns = [
    path("server_status", views.get_server_status, name="get_server_status"),
    path("", views.index)
]