# SPDX-FileCopyrightText: 2026 Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: CC0-1.0

FROM rabbitmq
RUN apt-get update && apt-get install -y wget
RUN rabbitmq-plugins enable rabbitmq_prometheus
EXPOSE 15672
CMD ["rabbitmq-server"]