# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import path

from .feeds import CapRSSFeed

urlpatterns = [
    path("<str:feed_id>/rss.xml", CapRSSFeed(), name="cap_feed"),
]