<!--
# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later
-->

# FOSS Public Alert Server

The goal of this project is to provide an open source server that allows desktop applications like kPublicAlerts (still beta)
and mobile applications such as [FOSS Warn](https://github.com/nucleus-ffm/foss_warn) to receive near real-time push notifications via
[UnifiedPush](https://unifiedpush.org/) about emergency alerts worldwide.

*a project in collaboration with KDE and the FOSS Warn Team*

This project is still in development and not yet ready for production!

## Server setup

The server consists of three parts:
* An off-the-shelf [PostGIS](https://postgis.net/) database server.
* The AlertHandler, which retrieves the alert sources and stores the alerts in the database
Stores alerts in the database and provides endpoints for retrieving alerts
* the SubscriptionHandler, with which you can register for an area to receive push notifications
* A celery worker who calls up the alert-fetching at regular intervals

### PostGIS setup

No special configuration is required, but there needs to be an empty database
and, depending on your setup, a corresponding database user.

### Aggregator service setup

The aggregator service uses [Django](https://www.djangoproject.com/) and needs a few other Python modules
as dependencies as well, see `publicAlertAggregator/requirements.txt`. Install those via your distribution or
`pip` (see also the [pip user guide](https://pip.pypa.io/en/stable/user_guide/)).

The aggregator service needs to be configured to find your PostGIS database. This
can be done in `publicAlertsAggregator/settings.py` or via environment variables.
* `POSTGRES_HOST`: IP address or host name of the PostGIS server
* `POSTGRES_DATABASE`: name of the PostGIS database
* `POSTGRES_USER`: name of the user on the PostGIS database
* `POSTGRES_PASSWORD`: password for connecting to the PostGIS database

The aggregator service is started as follows for local development:

```bash
python3 manage.py collectstatic
python3 manage.py migrate
python3 manage.py runserver 8000
```

The first two steps are only necessary when the static files or the database layout changed
respectively, you'll only need the last command otherwise.

For a production deployment, you'll likely want to put this behind a HTTP server,
see the [Django deployment documentation](https://docs.djangoproject.com/en/5.0/howto/deployment/).

### Celery setup
We use [celery](https://docs.celeryq.dev/) to dispatch tasks periodically in the background.
Celery requires a message transport (broker). We have chosen [rabbitmq](https://www.rabbitmq.com/).

```bash
pip install celery
pip install django-celery-beat

# start rabbitmq docker container
docker run -d -p 5672:5672 rabbitmq

# start celery 
celery -A foss_public_alert_server worker --loglevel=INFO

# start celery beat
celery -A foss_public_alert_server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
check out the official [manual](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)
