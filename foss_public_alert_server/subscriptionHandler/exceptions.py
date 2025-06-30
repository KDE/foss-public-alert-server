# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

class PushNotificationCheckFailed(Exception):
    pass

class PushNotificationException(Exception):
    pass

class PushNotificationTimeoutException(Exception):
    pass

class UnifiedPushServerIsBlacklisted(Exception):
    def __init__(self, domainname):
        self.domainname = domainname