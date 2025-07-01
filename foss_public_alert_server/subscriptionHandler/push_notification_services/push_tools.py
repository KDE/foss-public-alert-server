# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import tldextract
from datetime import datetime, timezone
from subscriptionHandler.models import ConnectionFlag
from ..exceptions import PushNotificationTimeoutException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setTimeoutFlag(distributor_url) -> None:
    """
    create a new timeout flag in the database. The flag is created from the domain name of the distributor_url
    :param distributor_url: the server url
    :return: None
    """
    extracted_domain = tldextract.extract(distributor_url)
    if extracted_domain.subdomain:
        push_server_url = f"{extracted_domain.subdomain}.{extracted_domain.domain}.{extracted_domain.suffix}"
    else:
        push_server_url = f"{extracted_domain.domain}.{extracted_domain.suffix}"
    flag = ConnectionFlag(
        hostname=push_server_url,
        time_out= True
    )
    flag.save()

def checkTimeoutFlag(distributor_url):
    """
    check for the given distributor url if the server has an active timeout flag
    :param distributor_url: the UnifiedPush endpoint
    :return: None
    :raise PushNotificationTimeoutException if the server has an active timeout flag
    """
    extracted_domain = tldextract.extract(distributor_url)
    if extracted_domain.subdomain:
        push_server_url = f"{extracted_domain.subdomain}.{extracted_domain.domain}.{extracted_domain.suffix}"
    else:
        push_server_url = f"{extracted_domain.domain}.{extracted_domain.suffix}"
    try:
        flag = ConnectionFlag.objects.get(hostname=push_server_url)
    except ConnectionFlag.DoesNotExist:
        return
    timedelta = datetime.now(timezone.utc) - flag.set_time_stamp
    # check if the flag has expired
    if timedelta.seconds > 300: # Expire the flag after 5 minutes
        logger.debug(f"Timeout flag {flag.hostname} has expired. Deleting...")
        flag.delete()
        return
    # if the flag is still valid, raise an exception
    if flag.time_out:
        logger.debug(f"Timeout flag for {push_server_url} has been set at {flag.set_time_stamp}")
        raise PushNotificationTimeoutException(f"Timeout flag has been set at {flag.set_time_stamp}")