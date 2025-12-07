# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

class PushNotificationCheckFailed(Exception):
    pass

class PushNotificationException(Exception):
    pass

class PushNotificationTimeoutException(Exception):
    pass

class PushNotificationExpiredException(Exception):
    """The push notification returned a 404 or 410 response.

    This indicates that the push notification subscription has expired,
    We can delete the subscription as well.
    """
    def __init__(self, reason):
        self.reason = reason

class UnifiedPushServerIsBlacklisted(Exception):
    def __init__(self, domainname):
        self.domainname = domainname