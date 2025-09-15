<!--
# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later
-->

# FOSS Public Alert Server

The FOSS Public Alert Server lets clients receive push notification via [UnifiedPush](https://unifiedpush.org/) about emergency and weather alerts worldwide.

This is made possible thanks to [OASIS' Common Alerting Protocol (CAP)](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html).
CAP alerts are used for a wide variety of emergencies. From alerts about extreme weather to alerts about contaminated drinking water to pandemics.

Our server aggregates hundreds of CAP Feeds published by alerting authorities worldwide. When finished, this server can be used with clients like [FOSS Warn](https://github.com/nucleus-ffm/foss_warn) and [KDE's alert integration](https://invent.kde.org/utilities/kpublicalerts) (still beta).

We have three main motivations. Firstly, we want to offer an easy-to-use alternative to propriety emergency apps to allow privacy- and freedom-focused people to receive emergency alerts. Secondly, we want to enable other developers to implement clients for different devices like desktop PCs, smart speakers, and Linux smartphones, and last but not least, we want to make traveling easier. While traveling, no one wants to search and install the local emergency app to receive emergency alerts in this country. With our solution, there is one app for the world.
 
This project aims to expand the existing and already used alerting infrastructure and is not a replacement for any part of it. Stay informed and safe!

*a project in collaboration with KDE and the FOSS Warn Team*

This project is still in development and not yet ready for production!

## Funding
*2024-10 until 2025-10*

> This project was funded through the [NGI0 Core Fund](https://nlnet.nl/core), a fund established by [NLnet](https://nlnet.nl/) with financial support from the European Commission's [Next Generation Internet](https://ngi.eu/) programme, under the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en) under grant agreement [No. 101092990](https://cordis.europa.eu/project/id/101092990).

<img src="https://nlnet.nl/logo/banner.svg" width=160>
&nbsp;&nbsp;
<img src="https://nlnet.nl/image/logos/NGI0Core_tag.svg" width=160>

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

# if you need more monitoring tools you can start rabbitmq with enabled management UI instead
docker run -d -p 5672:5672 rabbitmq:3-management 
# you can now vist the UI under http://container-IP:15672
# the default username is "guest" with the default password "guest"
# you can find the container IP if you run `docker inspect <container-id>`
# the container-id is displayed if you run `docker ps`

# to inspect the rabbitmq queue manually in a shell you can do
sudo docker exec -it [ccontainer-id] rabbitmqctl list_queues name messages messages_ready messages_unacknowledged

# start celery worker for alert parsing
celery -A foss_public_alert_server worker --loglevel=INFO -n alerts --concurrency 3

# start celery worker for sending push notifications
celery -A foss_public_alert_server worker  --loglevel=INFO -Q push_notifications -n notifications --concurrency 1

# if you have flower installed, you can start the celery monitoring tool with
celery -A foss_public_alert_server flower --port=5556
# you can now visit the flower under http://localhost:5556

# start celery beat
celery -A foss_public_alert_server beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
check out the official [manual](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)

## Docker setup
This repo contains a docker compose file that you can quickly start by:
```bash
# clone or download the repository
git clone https://invent.kde.org/webapps/foss-public-alert-server.git
# change the directory
cd foss-public-alert-server/compose 
# make sure the docker demon
# start the docker container in the background
docker compose up -d
# wait until the container is up, then create a django admin account
docker exec -it foss-public-alert-server-aggregator-1 python manage.py createsuperuser
# after that you should be able to visit the admin page
# via http://localhost:8000/admin
```
**Notice**
The default config is for _development only_, and not safely configured for deployments!