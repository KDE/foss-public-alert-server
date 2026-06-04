# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

class PushNotificationCheckFailed(Exception):
    pass


class PushNotificationException(Exception):
    error_code: str

    def __init__(self, error_code: str = "unknown"):
        self.error_code = str(error_code)


class PushNotificationTimeoutException(Exception):
    pass

class PushNotificationExpiredException(Exception):
    """The push notification returned a 404 or 410 response.

    This indicates that the push notification subscription has expired,
    We can delete the subscription as well.
    """
    def __init__(self, reason):
        self.reason = reason


class UnifiedPushTokenValidationException(Exception):
    """Emitted when validating a UnifiedPush token failed.

       Examples include invalid URLs, local addresses, or blacklisted push server.
    """
    def __init__(self, reason):
        self.reason = reason
