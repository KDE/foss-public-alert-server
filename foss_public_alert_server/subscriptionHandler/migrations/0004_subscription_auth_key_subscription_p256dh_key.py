# Generated by Django 5.1.3 on 2025-03-01 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptionHandler', '0003_rename_distributor_url_subscription_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='auth_key',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='p256dh_key',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
