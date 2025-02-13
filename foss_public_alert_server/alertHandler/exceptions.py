# SPDX-FileCopyrightText: Nucleus <nucleus-ffm@posteo.de>
# SPDX-License-Identifier: AGPL-3.0-or-later

class AlertExpiredException(BaseException):
    pass


class DatabaseWritingException(BaseException):
    """
    raised if something went wrong while writing in the database
    """
    pass


class AlertParameterException(BaseException):
    pass


class NoGeographicDataAvailableException(BaseException):
    """
    This exception is raised if we do not have geo information for this alert. This can be due to missing geocode
    translation
    """
    pass

class NothingChangedException(BaseException):
    """
    This exception is raised if a http request returns status code 304  Nothing changed
    """
    pass
