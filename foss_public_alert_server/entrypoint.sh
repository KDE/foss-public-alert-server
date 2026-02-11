#!/bin/bash
# SPDX-FileCopyrightText: 2022 Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: CC0-1.0

rm -rf /tmp/fpas-metrics
mkdir -p /tmp/fpas-metrics
export PROMETHEUS_MULTIPROC_DIR=/tmp/fpas-metrics

python3 manage.py collectstatic --clear --no-input
python3 manage.py migrate

celery -A foss_public_alert_server worker --loglevel=INFO -n general --concurrency 4 &
celery -A foss_public_alert_server worker --loglevel=INFO -Q push_notifications -n notifications --concurrency 1 &
celery -A foss_public_alert_server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &
celery -A foss_public_alert_server flower --url_prefix=flower &

uwsgi --socket :3032 --http :8000 --uid www-data --wsgi-file /app/foss_public_alert_server/wsgi.py
