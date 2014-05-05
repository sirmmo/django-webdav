# Portions (c) 2014, Alexander Klimenko <alex@erix.ru>
# All rights reserved.
#
# Copyright (c) 2011, SmartFile <btimby@smartfile.com>
# All rights reserved.
#
# This file is part of DjangoDav.
#
# DjangoDav is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DjangoDav is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with DjangoDav.  If not, see <http://www.gnu.org/licenses/>.


import httplib
from django.http import HttpResponse


# When possible, code returns an HTTPResponse sub-class. In some situations, we want to be able
# to raise an exception to control the response (error conditions within utility functions). In
# this case, we provide HttpError sub-classes for raising.


class ResponseException(Exception):
    """A base HTTP error class. This allows utility functions to raise an HTTP error so that
    when used inside a handler, the handler can simply call the utility and the correct
    HttpResponse will be issued to the client."""

    def __init__(self, response, *args, **kwargs):
        super(ResponseException, self).__init__('Response excepted', *args, **kwargs)
        self.response = response


class HttpResponsePreconditionFailed(HttpResponse):
    status_code = httplib.PRECONDITION_FAILED


class HttpResponseMediatypeNotSupported(HttpResponse):
    status_code = httplib.UNSUPPORTED_MEDIA_TYPE


class HttpResponseMultiStatus(HttpResponse):
    status_code = httplib.MULTI_STATUS


class HttpResponseNotImplemented(HttpResponse):
    status_code = httplib.NOT_IMPLEMENTED


class HttpResponseBadGateway(HttpResponse):
    status_code = httplib.BAD_GATEWAY


class HttpResponseCreated(HttpResponse):
    status_code = httplib.CREATED


class HttpResponseNoContent(HttpResponse):
    status_code = httplib.NO_CONTENT


class HttpResponseConflict(HttpResponse):
    status_code = httplib.CONFLICT


class HttpResponseLocked(HttpResponse):
    status_code = httplib.LOCKED


class HttpResponseUnAuthorized(HttpResponse):
    status_code = httplib.UNAUTHORIZED
