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
from djangodav.acls import FullAcl
from djangodav.locks import DummyLock

from djangodav.views import DavView

from django.conf.urls import url

from samples.fs.resources import TempDirWebDavResource
from samples.db.resources import MyDBDavResource
from samples.auth.views.rest import RestAuthDavView
from samples.auth.views.tasty import TastyAuthDavView


urlpatterns = [
    # Mirroring tmp folder
    url(r'^fs(?P<path>.*)$', DavView.as_view(resource_class=TempDirWebDavResource, lock_class=DummyLock, acl_class=FullAcl)),
    # Db file keeper
    url(r'^db(?P<path>.*)$', DavView.as_view(resource_class=MyDBDavResource, lock_class=DummyLock, acl_class=FullAcl)),

    # REST framework auth
    url(r'^auth/rest(?P<path>.*)$', RestAuthDavView.as_view(resource_class=TempDirWebDavResource, lock_class=DummyLock, acl_class=FullAcl)),
    # Tastypie auth
    url(r'^auth/tasty(?P<path>.*)$', TastyAuthDavView.as_view(resource_class=TempDirWebDavResource, lock_class=DummyLock, acl_class=FullAcl)),
]
