# Generated by Django 5.1.1 on 2024-11-09 11:10

import datetime
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptionHandler", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="last_heartbeat",
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
    ]
