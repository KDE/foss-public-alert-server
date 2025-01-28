# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("subscribe", views.subscribe, name="subscribe"),
    path("update_subscription", views.update_subscription, name="update_subscription"),
    path("unsubscribe", views.unsubscribe, name="unsubscribe"),
    path("heartbeat", views.heartbeat, name="heartbeat")
]