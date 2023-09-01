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
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from djangodav.responses import HttpResponseUnAuthorized

try:
    import rest_framework
    from rest_framework.exceptions import APIException
except ImportError:
    rest_framework = None


class RequestWrapper(object):
    """ simulates django-rest-api request wrapper """
    def __init__(self, request):
        self._request = request
    def __getattr__(self, attr):
        return getattr(self._request, attr)
    
    
class RestAuthViewMixIn(object):
    authentications = NotImplemented

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        assert rest_framework is not None, "django rest framework is not installed."
        if request.method.lower() != 'options':
            user_auth_tuple = None
            for auth in self.authentications:
                try:
                    user_auth_tuple = auth.authenticate(RequestWrapper(request))
                except APIException as e:
                    return HttpResponse(e.detail, status=e.status_code)
                else:
                    if user_auth_tuple is None:
                        continue # try next authenticator 
                    else:
                        break    # we got auth, so stop trying

            if user_auth_tuple is not None:
                user, auth = user_auth_tuple
            else:
                resp = HttpResponseUnAuthorized("Not Authorised")
                resp['WWW-Authenticate'] = self.authentications[0].authenticate_header(request)
                return resp

            request.user = user
            request.auth = auth
        return super(RestAuthViewMixIn, self).dispatch(request, *args, **kwargs)
