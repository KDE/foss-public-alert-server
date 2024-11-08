# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import path

from . import views

urlpatterns = [
    path("status", views.generate_source_status_page, name="status_page"),
    path("", views.index)
]