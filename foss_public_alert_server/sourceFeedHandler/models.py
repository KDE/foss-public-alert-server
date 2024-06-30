from django.db.models.signals import post_save
from django.dispatch import receiver

from django.db import models
import uuid
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from alertHandler.DWD_CAP_parser import DWDCAPParser
from django.conf import settings


# Create your models here.
class CAPFeedSource(models.Model):
    """
    - id: unique id of the feed source in database
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_id = models.CharField(max_length=255)
    code = models.CharField(max_length=255) # @todo there can be more then one entry here
    name = models.CharField(max_length=255)
    logo = models.CharField(max_length=255, null=True)
    guid = models.CharField(max_length=255, null=True)
    register_url = models.CharField(max_length=255, null=True)
    source_is_official = models.BooleanField(null=True)
    cap_alert_feed = models.CharField(max_length=255)
    cap_alert_feed_status = models.CharField(max_length=255)
    authorityCountry = models.CharField(max_length=255)
    authorityAbbrev = models.CharField(max_length=255)
    feedSource = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    ignore = models.BooleanField(null=True)

    last_fetch_status = models.BooleanField(null=True)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_periodic_task()

    def create_periodic_task(self):
        if self.format == "DWD-Zip":
            parser = DWDCAPParser(self)
            schedule = self.get_or_create_interval()
            task = PeriodicTask.objects.create(
                interval=schedule,
                name=f'Periodic task for - {self.id}',
                task=parser.get_feed(),
            )
            task.save()


    def get_or_create_interval(self):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=settings.DEFAULT_UPDATE_PERIOD_FOR_CAP_FEEDS,
            period=IntervalSchedule.SECONDS,
        )
        return schedule



