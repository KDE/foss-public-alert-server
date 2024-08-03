import datetime
from time import sleep

from celery import shared_task

from .models import Alert


@shared_task()
def test_celery():
    for i in range(0, 11):
        print(i)
        sleep(1)
    return "Task complete!"


def check_if_alert_is_expired(expire_time:datetime) -> bool:
    """
    check if the expire_time is later than current time
    :param expire_time: the expire_time of the alert
    :return: true if alert is expired, false if not
    """
    return expire_time > datetime.datetime.now(datetime.timezone.utc)


@shared_task(name="task.remove_expired_alerts")
def remove_expired_alerts() -> bool:
    """
    check for every alert if it is expired and delete every expired alert
    called by a periodic celery task
    :return:
    """
    alerts = Alert.objects
    for alert in alerts:
        if check_if_alert_is_expired:
            print(f"delete alert {alert.alert_id}")
            alerts.objects.filter(id=alert.id).delete()
            # the delete() sends also a signal to a class methode (Alert.auto_delete_capdata_on_delete)
            # to also delete the stored cap data
    return True
