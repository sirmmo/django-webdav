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


class HttpError(Exception):
    """A base HTTP error class. This allows utility functions to raise an HTTP error so that
    when used inside a handler, the handler can simply call the utility and the correct
    HttpResponse will be issued to the client."""
    status_code = 500

    def get_response(self):
        """Creates an HTTPResponse for the given status code."""
        return HttpResponse(self.message, status=self.status_code)


class HttpCreated(HttpError):
    status_code = httplib.CREATED


class HttpNoContent(HttpError):
    status_code = httplib.NO_CONTENT


class HttpNotModified(HttpError):
    status_code = httplib.NOT_MODIFIED


class HttpMultiStatus(HttpError):
    status_code = httplib.MULTI_STATUS


class HttpNotAllowed(HttpError):
    status_code = httplib.METHOD_NOT_ALLOWED


class HttpResponseBadRequest(HttpError):
    status_code = httplib.BAD_REQUEST


class HttpResponseNotAllowed(HttpError):
    status_code = httplib.METHOD_NOT_ALLOWED


class HttpConflict(HttpError):
    status_code = httplib.CONFLICT


class HttpPreconditionFailed(HttpError):
    status_code = httplib.PRECONDITION_FAILED


class HttpResponsePreconditionFailed(HttpResponse):
    status_code = httplib.PRECONDITION_FAILED


class HttpBadGateway(HttpError):
    status_code = httplib.BAD_GATEWAY


class HttpResponseMediatypeNotSupported(HttpResponse):
    status_code = httplib.UNSUPPORTED_MEDIA_TYPE


class HttpResponseMultiStatus(HttpResponse):
    status_code = httplib.MULTI_STATUS


class HttpResponseNotImplemented(HttpResponse):
    status_code = httplib.MULTI_STATUS


class HttpResponseBadGateway(HttpResponse):
    status_code = httplib.BAD_GATEWAY


class HttpResponseCreated(HttpResponse):
    status_code = httplib.CREATED


class HttpResponseNoContent(HttpResponse):
    status_code = httplib.NO_CONTENT

class HttpMediatypeNotSupported(HttpError):
    status_code = httplib.UNSUPPORTED_MEDIA_TYPE

class HttpResponseConflict(HttpResponse):
    status_code = httplib.CONFLICT
