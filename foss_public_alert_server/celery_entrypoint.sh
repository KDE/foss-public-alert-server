#!/bin/bash
# SPDX-FileCopyrightText: 2026 Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: CC0-1.0

celery -A foss_public_alert_server worker --loglevel=INFO -n general --concurrency 4 &
celery -A foss_public_alert_server worker --loglevel=INFO -Q push_notifications -n notifications --concurrency 1 &
celery -A foss_public_alert_server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &
# do not run each command in background otherwise the container will stop and restart all the time.
celery -A foss_public_alert_server flower --url_prefix=flower
