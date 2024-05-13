from django.contrib import admin
from .models import Alert
from django.contrib.gis import admin

# Register your models here.

class AlertAdmin(admin.GISModelAdmin):
    list_display = ('id', 'source_id', 'alert_id', 'issue_time', 'expire_time')

admin.site.register(Alert, AlertAdmin)

