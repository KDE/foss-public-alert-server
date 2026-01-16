# SPDX-FileCopyrightText: 2022 Volker Krause <vkrause@kde.org>
# SPDX-License-Identifier: CC0-1.0

FROM python:3.10-bullseye
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get -y install libgdal-dev
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app
RUN mkdir -p /app/alertHandler/static/maplibre

ARG MAPLIBRE_VERSION="latest"
# TODO should be --fail-with-body, once we have a sufficiently new curl in this image
RUN curl --fail -L https://unpkg.com/maplibre-gl@${MAPLIBRE_VERSION}/dist/maplibre-gl.css > /app/alertHandler/static/maplibre/maplibre-gl.css
RUN curl --fail -L https://unpkg.com/maplibre-gl@${MAPLIBRE_VERSION}/dist/maplibre-gl.js > /app/alertHandler/static/maplibre/maplibre-gl.js

ARG REVISION=""
RUN echo -n "${REVISION}" > /app/build-revision

EXPOSE 8000/tcp
CMD /app/entrypoint.sh
