# Generated by Django 5.1.1 on 2025-02-22 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alertHandler", "0002_alert_cap_data_modified"),
    ]

    operations = [
        migrations.AddField(
            model_name="alert",
            name="event",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="alert",
            name="msg_type",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="alert",
            name="severity",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="alert",
            name="status",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="alert",
            name="urgency",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
