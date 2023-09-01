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


class TastypieAuthViewMixIn(object):
    authentication = NotImplemented

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):

        if request.method.lower() != 'options':
            auth_result = self.authentication.is_authenticated(request)

            if isinstance(auth_result, HttpResponse):
                return auth_result

            if auth_result is not True:
                return HttpResponseUnAuthorized()

        return super(TastypieAuthViewMixIn, self).dispatch(request, *args, **kwargs)
