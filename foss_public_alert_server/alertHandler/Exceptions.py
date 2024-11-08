# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

class AlertExpiredException(BaseException):
    pass


class DatabaseWritingException(BaseException):
    pass


class AlertParameterException(BaseException):
    pass


class NoGeographicDataAvailableException(BaseException):
    pass
