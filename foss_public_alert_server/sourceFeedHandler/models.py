# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import models
import uuid

from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from django.conf import settings


# Create your models here.
class CAPFeedSource(models.Model):
    """
    - id: unique id of the feed source in database
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_id = models.CharField(max_length=255)
    code = models.CharField(max_length=255)  # @todo there can be more then one entry here
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
    last_fetch_duration = models.DurationField(null=True)
    missing_geo_information = models.BooleanField(null=True)
    feed_warnings = models.CharField(max_length=255, null=True)
    last_e_tag = models.CharField(max_length=255, null=True)
    periodic_task_name = models.CharField(max_length=255, null=True)
    latest_published_alert_datetime = models.DateTimeField(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # create periodic tasks for every feeds that is not ignored and operating
        if not self.ignore and self.cap_alert_feed_status == "operating":
            self.create_periodic_task()

    def create_periodic_task(self) -> None:
        """
        create a periodic task for this feed source
        :return: None
        """
        schedule = self.get_or_create_interval()
        task_name = f'periodic feed updater for - {self.source_id} - {self.id}'
        # only create task if it not already exists and if the feed is not set to ignore
        if not PeriodicTask.objects.filter(name=task_name).exists():
            task = PeriodicTask.objects.create(
                interval=schedule,
                name=task_name,
                task='task.create_parser_and_get_feed',
                args=f'["{self.id}", "{self.format}"]',
            )
            task.save()
            self.periodic_task_name = task_name

    @staticmethod
    def get_or_create_interval():
        """
        get or create an interval for the periodic scheduler
        uses settings.DEFAULT_UPDATE_PERIOD_FOR_CAP_FEEDS as period
        :return:
        """
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=settings.DEFAULT_UPDATE_PERIOD_FOR_CAP_FEEDS,
            period=IntervalSchedule.SECONDS,
        )
        return schedule


@receiver(models.signals.post_delete, sender=CAPFeedSource)
def auto_delete_periodic_task_on_delete(sender, instance:CAPFeedSource, **kwargs) -> None:
    """
    called if CAPFeedSource entry is deleted. Deletes also the periodic task
    :param instance: The actual instance being deleted.
    :param kwargs:
    :return: None
    """
    if PeriodicTask.objects.filter(name=instance.periodic_task_name).exists():
        PeriodicTask.objects.filter(name=instance.periodic_task_name).delete()
