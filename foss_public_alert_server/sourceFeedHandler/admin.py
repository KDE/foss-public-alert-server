from django.contrib import admin
from .models import CAPFeedSource
# Register your models here.

class CAPSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_id', 'name')

admin.site.register(CAPFeedSource, CAPSourceAdmin)