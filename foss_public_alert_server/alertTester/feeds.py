# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib.syndication.views import Feed
from .models import TestAlert, CapFeed

class CapRSSFeed(Feed):
    description_template = "templates/cap_rss_feed_template.html"

    def get_object(self, request, feed_id):
        return CapFeed.objects.get(source_id=feed_id)

    def title(self, obj):
        return f"Alert feed from {obj.source_id}"

    def link(self, obj):
        return f"/feed/{obj.source_id}"

    def description(self, obj):
        return ("This feed only contains technical test alerts from the FOSS Public Alert Server. There is no real danger. "
                "This feed is not associated with any official government.")

    def item_link(self, item):
        return f"/cap/{item.cap_data}"

    def item_title(self, item):
        return item.headline

    def item_description(self, item):
        return item.description

    def items(self, obj):
        return TestAlert.objects.filter(source_id=obj.source_id).order_by("sent")