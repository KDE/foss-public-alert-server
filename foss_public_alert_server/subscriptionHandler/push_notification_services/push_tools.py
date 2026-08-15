# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import tldextract
from datetime import datetime, timezone

from configuration.models import AppSetting
from subscriptionHandler.models import ConnectionFlag
from ..exceptions import PushNotificationTimeoutException
from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_timeout_flag(distributor_url:str, flag_type:ConnectionFlag.FlagType, error_msg:str) -> None:
    """
    create a new timeout flag in the database. The flag is created from the domain name of the distributor_url
    :param distributor_url: the server url
    :param flag_type: the connection flag type
    :param error_msg: the error message why the flag is set
    :return: None
    """
    extracted_domain = tldextract.extract(distributor_url.lower())
    if extracted_domain.subdomain:
        push_server_url = f"{extracted_domain.subdomain}.{extracted_domain.domain}.{extracted_domain.suffix}"
    else:
        push_server_url = f"{extracted_domain.domain}.{extracted_domain.suffix}"
    # check if there is already an entry for this url, and if not, create a new one
    if not ConnectionFlag.objects.filter(hostname=push_server_url).exists():
        match flag_type:
            case ConnectionFlag.FlagType.TIME_OUT:
                expire_datetime = datetime.now(timezone.utc) + settings.CONNECTION_FLAG_GENERAL_EXPIRATION_SECONDS

            case ConnectionFlag.FlagType.RATE_LIMIT:
                expire_datetime = datetime.now(timezone.utc) + settings.CONNECTION_FLAG_RATE_LIMIT_EXPIRATION_SECONDS

        ConnectionFlag.objects.filter(hostname=push_server_url).update_or_create(
            set_time_stamp=datetime.now(timezone.utc),
            expire_time_stamp=expire_datetime,
            defaults={"hostname": push_server_url,
                      "type": flag_type,
                      "error_message": error_msg[:255]})


def check_timeout_flag(distributor_url:str) -> None:
    """
    check for the given distributor url if the server has an active timeout flag
    :param distributor_url: the UnifiedPush endpoint
    :return: None
    :raise PushNotificationTimeoutException if the server has an active timeout flag
    """
    extracted_domain = tldextract.extract(distributor_url.lower())
    if extracted_domain.subdomain:
        push_server_url = f"{extracted_domain.subdomain}.{extracted_domain.domain}.{extracted_domain.suffix}"
    else:
        push_server_url = f"{extracted_domain.domain}.{extracted_domain.suffix}"
    try:
        flag = ConnectionFlag.objects.get(hostname=push_server_url)
    except ConnectionFlag.DoesNotExist:
        return

    if ConnectionFlag.expire_time_stamp < datetime.now(timezone.utc):
        logger.debug(f"{flag.type} flag {flag.hostname} has expired. Deleting...")
        flag.delete()
        return

    # if the flag is still valid, raise an exception
    logger.debug(f"Timeout flag for {push_server_url} has been set at {flag.set_time_stamp}")
    raise PushNotificationTimeoutException(f"{flag.type} flag for {push_server_url} has been set at {flag.set_time_stamp}")