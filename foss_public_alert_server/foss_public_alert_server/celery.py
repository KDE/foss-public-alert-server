# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from celery.signals import worker_ready
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foss_public_alert_server.settings')

app = Celery('foss_public_alert_server', broker=settings.AMQP_URL)  # pyamqp://guest@localhost//

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# set timelimit for periodic background task to 30s soft and 60s hard
app.control.time_limit('task.create_parser_and_get_feed', soft=30, hard=60, reply=True)


@app.task(bind=True, ignore_result=True, name="debugtask")
def debug_task(self):
    print(f'Request: {self.request!r}')

@worker_ready.connect
def execute_at_startup(sender, **k) -> None:
    """
    This task is executed when the application is started for the first time. Here we schedule the task to load the feed sources.
    This is done to avoid having to wait until midnight for the feed sources to be retrieved for the first time.
    :param sender:
    :param k:
    :return: None
    """
    with sender.app.connection() as conn:
        logger.info("Initialize feed sources...")
        sender.app.send_task('task.reload_feed_sources_and_update_database')
        logger.info("Store default settings in database...")
        sender.app.send_task('task.store_default_settings_in_database')


# create periodic tasks to remove old subscriptions
app.conf.beat_schedule = {
    'remove_inactive_subscription_every_day_at_midnight': {
        'task': 'task.remove_old_subscriptions',
        'schedule': crontab(minute="0", hour="0"),
    },
    'update_feed_sources_every_day_at_midnight': {
        'task': 'task.reload_feed_sources_and_update_database',
        'schedule': crontab(minute="0", hour="0"),
    },
    'remove_expired_alerts_every_hour': {
        'task': 'task.remove_expired_alerts',
        'schedule': crontab(minute="0", hour="*"),
    },
}

app.conf.timezone = 'UTC' # @todo fix timezone
