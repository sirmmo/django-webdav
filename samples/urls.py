# Copyright (c) 2011, SmartFile <btimby@smartfile.com>
# All rights reserved.
#
# This file is part of django-webdav.
#
# Foobar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with django-webdav.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import *
from samples.custom.server import CustomDavServer

urlpatterns = patterns('',
    # This will simply export the directory configured by DAV_ROOT in settings.py
    (r'^simple(?P<path>.*)$', 'django_webdav.views.export'),
    # This customized version will use a DavServer subclass.
    # This would be useful if authentication is being done via middlware.
    (r'^custom(?P<path>.*)$', 'django_webdav.views.export', { 'server_class': CustomDavServer }),
    # This more advanced version will use a customized view.
    # This would be useful if authentication is being done via decorators.
    (r'^advanced(?P<path>.*)$', 'samples.advanced.views.export'),
)
