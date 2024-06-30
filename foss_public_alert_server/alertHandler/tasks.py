from celery import shared_task

from . import abstract_CAP_parser
from .XML_CAP_parser import XMLCAPParser
from .MOWAS_CAP_parser import MoWaSCapParser
from .DWD_CAP_parser import DWDCAPParser
from time import sleep

from foss_public_alert_server.celery import app as celery_app
from django.conf import settings

from sourceFeedHandler.models import CAPFeedSource



""""
@shared_task(name="fetch_alert_sources")
def fetch_alert_sources():
    print("fetching alert sources...")
    i = 0
    for feedReader in feedReaders:
        feedReader.get_feed()
        # if i > 10:
        #    break
        # i += 1
        break # @todo test only the first one, remove line to fetch all sources
"""

@shared_task()
def test_celery():
    for i in range(0, 11):
        print(i)
        sleep(1)
    return "Task complete!"


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    create a celery task for every feed to run every 60s
    :param sender:
    :param kwargs:
    :return:
    """
    print("setup periodic tasks...")
    print(CAPFeedSource.objects)
    for feed in CAPFeedSource.objects.all():
        parser:abstract_CAP_parser = None
        print(feed.source_id)
        match feed.format:
            case "rss or atom":
                print("its atom")
            case "de-mowas":
                print("its mowas")
                parser = MoWaSCapParser(feed)
            case "DWD-Zip":
                print("its dwd")
                parser = DWDCAPParser(feed)

        if parser is not None:
            sender.add_periodic_task(settings.DEFAULT_UPDATE_PERIOD_FOR_CAP_FEEDS, parser.get_feed(), name='Periodic task for {}!'.format(feed.source_id))


