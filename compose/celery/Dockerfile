# SPDX-FileCopyrightText: 2026 Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: CC0-1.0

FROM python:3.10-bullseye
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get -y install libgdal-dev
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app

CMD /app/celery_entrypoint.sh
