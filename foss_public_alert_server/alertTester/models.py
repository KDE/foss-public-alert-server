# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later
from random import choices

from django.conf import settings
from django.contrib.gis.db import models
from django.core.files.storage import FileSystemStorage
from django.dispatch import receiver
import uuid
import os
from .cap_xml_builder import build_alert
from django.core.files.base import ContentFile

class CapFeed(models.Model):
    """
    Defines a CAP rss feed
    source_id: the id used to identify this feed.
    """
    source_id = models.CharField(primary_key=True, max_length=255)

def alert_upload_path(instance, filename) -> str:
    """
    return the upload path for cap alerts. Do not change the methode parameters
    as this methode is called by django

    :param instance: current instance of the alert where the file is being attached
    :param filename: the filename that was originally given to the file
    :return: filepath in Unix-style
    """
    return f"feeds/{instance.source_id.source_id}/{filename}"

class TestAlert(models.Model):
    class MsgType(models.TextChoices):
        Alert = "Alert"
        Update = "Update"
        Cancel = "Cancel"
        Ack = "Ack"
        Error ="Error"

    class Status(models.TextChoices):
        Actual = "Actual"
        Exercise = "Exercise"
        System = "System"
        Test = "Test"
        Draft = "Draft"

    class Scope(models.TextChoices):
        Public = "Public"
        Restricted = "Restricted"
        Private = "Private"

    class Urgency(models.TextChoices):
        Immediate = "Immediate"
        Expected = "Expected"
        Future = "Future"
        Past = "Past"
        Unknown = "Unknown"

    class Severity(models.TextChoices):
        Extreme = "Extreme"
        Severe = "Severe"
        Moderate = "Moderate"
        Minor = "Minor"
        Unknown = "Unknown"

    class Certainty(models.TextChoices):
        Observed = "Observed"
        Likely = "Likely"
        Possible = "Possible"
        Unlikely = "Unlikely"
        Unknown = "Unknown"

    class Category(models.TextChoices):
        Geo = "Geo"
        Met = "Met"
        Safety = "Safety"
        Security = "Security"
        Rescue = "Rescue"
        Fire = "Fire"
        Health = "Health"
        Env = "Env"
        Transport = "Transport"
        Infra = "Infra"
        CBRNE = "CBRNE"
        Other = "Other"

    """
    defines a simplified CAP alert for testing purposes
    
    source_id: used to identify the alert feed
    alert_id: unique ID of this alert
    sender: The identifier of the sender of the alert message 
    sent: The time and date of the origination of the alert message
    status: The code denoting the appropriate handling of the alert message 
    msgType: The code denoting the nature of the alert message 
    scope: The code denoting the intended distribution of the alert message 
    cap_data: path to the XML file 
    category: The code denoting the category of the subject event of the alert message
    event: The text denoting the type of the subject event of the alert message 
    urgency: The code denoting the urgency of the subject event of the alert message 
    severity: The code denoting the severity of the subject event of the alert message 
    certainty: The code denoting the certainty of the subject event of the alert message 
    onset: The expected time of the beginning of the subject event of the alert message 
    expires: The expiry time of the information of the alert message 
    headline: The text headline of the alert message 
    description: The text describing the subject event of the alert message
    areaDesc: The text describing the affected area of the alert message
    polygon: The paired values of points defining a polygon that delineates the affected area of the alert message 
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_id = models.ForeignKey(CapFeed, on_delete=models.CASCADE, null=True)
    alert_id = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    sent = models.DateTimeField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.Test)
    msg_type = models.CharField(max_length=15, choices=MsgType.choices, default=MsgType.Alert)
    scope = models.CharField(max_length=15, choices=Scope.choices, default=Scope.Public)
    # @TODO(Nucleus): We have to find a solution to override old files. Currently, Django creates a new file name if you press save in the admin view. This results in dead files in storage.
    cap_data = models.FileField(upload_to=alert_upload_path, null=True)
    # an alert can have multiple categories. If needed we have to changes the model to support that
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.Other)
    event = models.CharField(max_length=255)
    urgency = models.CharField(max_length=15, choices=Urgency.choices, default=Urgency.Unknown)
    severity = models.CharField(max_length=15, choices=Severity.choices, default=Severity.Unknown)
    certainty = models.CharField(max_length=15, choices=Certainty.choices, default=Certainty.Unknown)
    onset = models.DateTimeField(null=True)
    expires = models.DateTimeField(null=True)
    headline = models.CharField(max_length=255)
    description = models.CharField(max_length=512)
    areaDesc = models.CharField(max_length=255)
    polygon = models.MultiPolygonField(null=True, spatial_index=True)

    def save(self, *args, **kwargs):
        # build CAP XML file store it in cap_data
        self.cap_data.save(f"{self.alert_id}.xml", ContentFile(build_alert(self)), save=False)
        super().save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=TestAlert)
def auto_delete_capdata_on_delete(sender, instance: TestAlert, **kwargs) -> None:
    """
    called if an TestAlert entry is deleted. Deletes also the locally stored cap data
    :param instance: The actual instance being deleted.
    :param kwargs:
    :return: None
    """
    if instance.cap_data:
        if os.path.isfile(instance.cap_data.path):
            os.remove(instance.cap_data.path)