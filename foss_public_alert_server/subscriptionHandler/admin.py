# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib import admin
from .models import Subscription

# Register your models here.
admin.site.register(Subscription)
