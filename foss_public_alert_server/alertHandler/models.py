# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-FileCopyrightText: Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import models
from django.dispatch import receiver
from django.contrib.gis.db import models
import os
import uuid


# Create your models here.

def alert_upload_path(instance, filename) -> str:
    """
    return the upload path for cap alerts. Do not change the methode parameters
    as this methode is called by django

    :param instance: current instace of the alert where the file is being attached
    :param filename: the filename that was originally given to the file
    :return: filepath in Unix-style
    """
    return f"alerts/{instance.source_id}/{filename}"


class Alert(models.Model):
    """
    - id: unique id of the alert in database
    - source_id: the source from where we got the alert
    - alert_id: the id of the alert
    - bounding_box: coordinates of the area of the alert
    - cap_data: file of the CAP data in XML
    - cap_data_modified: true if we had to modify the original cap data
    - issue_time: the time of creation of the alert
    - expire_time: time at which the alert expires
    - source_url: the url of the original CAP data
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_id = models.CharField(max_length=255)
    alert_id = models.CharField(max_length=255)
    bounding_box = models.PolygonField()
    cap_data = models.FileField(upload_to=alert_upload_path, null=True)
    cap_data_modified = models.BooleanField(null=True)
    issue_time = models.DateTimeField()
    expire_time = models.DateTimeField(null=True)
    source_url = models.CharField(max_length=255, null=True)

    class Meta:
        constraints = [models.UniqueConstraint('source_id', 'alert_id', name='source_id-alert_id-unique')]

    def __str__(self):
        result = ""
        result += "id: " + str(self.id) + "\n"
        result += "source id:" + str(self.alert_id) + "\n"
        # @todo
        return result


@receiver(models.signals.post_delete, sender=Alert)
def auto_delete_capdata_on_delete(sender, instance:Alert, **kwargs) -> None:
    """
    called if Alert entry is deleted. Deletes also the locally stored cap data
    :param instance: The actual instance being deleted.
    :param kwargs:
    :return: None
    """
    if instance.cap_data:
        if os.path.isfile(instance.cap_data.path):
            os.remove(instance.cap_data.path)

