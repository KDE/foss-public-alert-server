# Generated by Django 5.1.3 on 2025-06-30 19:30

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('subscriptionHandler', '0006_connectionflags'), ('subscriptionHandler', '0007_rename_connectionflags_connectionflag')]

    dependencies = [
        ('subscriptionHandler', '0005_subscription_error_counter_and_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConnectionFlag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hostname', models.CharField(max_length=255)),
                ('set_time_stamp', models.DateTimeField(default=datetime.datetime.now)),
                ('time_out', models.BooleanField()),
            ],
        ),
    ]
