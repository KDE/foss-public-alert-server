# Generated by Django 5.1.3 on 2024-12-21 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sourceFeedHandler', '0002_capfeedsource_latest_published_alert_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='capfeedsource',
            name='feed_warnings',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='capfeedsource',
            name='last_e_tag',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='capfeedsource',
            name='last_fetch_duration',
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='capfeedsource',
            name='last_fetch_status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='capfeedsource',
            name='latest_published_alert_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='capfeedsource',
            name='logo',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='capfeedsource',
            name='missing_geo_information',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='capfeedsource',
            name='register_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
