import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foss_public_alert_server.settings')

app = Celery('foss_public_alert_server', broker='amqp://localhost')  # pyamqp://guest@localhost//

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True, name="debugtask")
def debug_task(self):
    print(f'Request: {self.request!r}')


# create periodic tasks to fetch the alert source
# every 60 seconds
app.conf.beat_schedule = {
    'fetch_alert_sources_every_60s': {
        'task': 'fetch_alert_sources',
        'schedule': 60.0,
    },
    'remove_inactive_subscription_every_day_at_midnight': {
        'task': 'remove_old_subscriptions',
        'schedule': crontab(minute="0", hour="0"),
    }
}

app.conf.timezone = 'UTC' # @todo fix timezone
