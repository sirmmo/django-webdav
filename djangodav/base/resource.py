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


from djangodav.utils import url_join


class BaseDavResource(object):
    base_url = None

    def __init__(self, path):
        self.path = []
        path = path.strip("/")
        if path:
            self.path = path.split("/")

    def get_path(self):
        return "/".join(self.path) + ("/" * self.isdir())

    def get_url(self):
        return url_join(self.base_url, self.get_path())

    def get_name(self):
        return self.path[-1]

    def get_dirname(self):
        path = self.path[:-1]
        return "/" + "/".join(path) + "/" if path else ""

    def get_parent(self):
        return self.__class__(self.get_dirname())

    def get_descendants(self, depth=1, include_self=True):
        """Return an iterator of all descendants of this resource."""
        if include_self:
            yield self
        # If depth is less than 0, then it started out as -1.
        # We need to keep recursing until we hit 0, or forever
        # in case of infinity.
        if depth != 0:
            for child in self.get_children():
                for desc in child.get_descendants(depth=depth-1, include_self=True):
                    yield desc

    def copy(self,  destination, depth=0):
        raise NotImplementedError()

    def move(self,  destination):
        raise NotImplementedError()

    def write(self, content):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    def isdir(self):
        raise NotImplementedError()

    def isfile(self):
        raise NotImplementedError()

    def exists(self):
        raise NotImplementedError()

    def get_size(self):
        raise NotImplementedError()

    def get_ctime_stamp(self):
        raise NotImplementedError()

    def get_ctime(self):
        raise NotImplementedError()

    def get_mtime_stamp(self):
        raise NotImplementedError()

    def get_mtime(self):
        raise NotImplementedError()

    def get_children(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

    def mkdir(self):
        raise NotImplementedError()

    def get_etag(self):
        raise NotImplementedError()
