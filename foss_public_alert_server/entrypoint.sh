#!/bin/bash
# SPDX-FileCopyrightText: 2022 Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: CC0-1.0

python3 manage.py collectstatic --clear --no-input
python3 manage.py migrate

celery -A foss_public_alert_server worker --loglevel=INFO &
celery -A foss_public_alert_server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &

uwsgi --socket :3032 --http :8000 --uid www-data --wsgi-file /app/foss_public_alert_server/wsgi.py
