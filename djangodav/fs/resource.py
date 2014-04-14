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
import hashlib
import mimetypes
import os
import datetime
import shutil
import urllib

from django.http import HttpResponse
from django.utils.http import http_date

from djangodav.base.resource import BaseDavResource
from djangodav.base.response import ResponseException
from djangodav.utils import safe_join, url_join


class BaseFSDavResource(BaseDavResource):
    """Implements an interface to the file system. This can be subclassed to provide
    a virtual file system (like say in MySQL). This default implementation simply uses
    python's os library to do most of the work."""

    root = None

    def get_abs_path(self):
        """Return the absolute path of the resource. Used internally to interface with
        an actual file system. If you override all other methods, this one will not
        be used."""
        return os.path.join(self.root, *self.path)

    def isdir(self):
        """Return True if this resource is a directory (collection in WebDAV parlance)."""
        return os.path.isdir(self.get_abs_path())

    def isfile(self):
        """Return True if this resource is a file (resource in WebDAV parlance)."""
        return os.path.isfile(self.get_abs_path())

    def exists(self):
        """Return True if this resource exists."""
        return os.path.exists(self.get_abs_path())

    def get_size(self):
        """Return the size of the resource in bytes."""
        return os.path.getsize(self.get_abs_path())

    def get_ctime_stamp(self):
        """Return the create time as UNIX timestamp."""
        return os.stat(self.get_abs_path()).st_ctime

    def get_ctime(self):
        """Return the create time as datetime object."""
        return datetime.datetime.fromtimestamp(self.get_ctime_stamp())

    def get_mtime_stamp(self):
        """Return the modified time as UNIX timestamp."""
        return os.stat(self.get_abs_path()).st_mtime

    def get_mtime(self):
        """Return the modified time as datetime object."""
        return datetime.datetime.fromtimestamp(self.get_mtime_stamp())

    def get_children(self):
        """Return an iterator of all direct children of this resource."""
        for child in os.listdir(self.get_abs_path()):
            yield self.__class__(self.server, os.path.join(self.path, child))

    def write(self, content):
        raise NotImplemented

    def read(self):
        raise NotImplemented

    def delete(self):
        """Delete the resource, recursive is implied."""
        if self.isdir():
            for child in self.get_children():
                child.delete()
            os.rmdir(self.get_abs_path())
        elif self.isfile():
            os.remove(self.get_abs_path())

    def mkdir(self):
        """Create a directory in the location of this resource."""
        os.mkdir(self.get_abs_path())

    def copy(self, destination, depth=0):
        """Called to copy a resource to a new location. Overwrite is assumed, the DAV server
        will refuse to copy to an existing resource otherwise. This method needs to gracefully
        handle a pre-existing destination of any type. It also needs to respect the depth
        parameter. depth == -1 is infinity."""
        if self.isdir():
            if destination.isfile():
                destination.delete()
            if not destination.isdir():
                destination.mkdir()
            # If depth is less than 0, then it started out as -1.
            # We need to keep recursing until we hit 0, or forever
            # in case of infinity.
            if depth != 0:
                for child in self.get_children():
                    child.copy(self.__class__(self.server, safe_join(destination.path, child.get_name())),
                               depth=depth-1)
        else:
            if destination.isdir():
                destination.delete()
            shutil.copy(self.get_abs_path(), destination.get_abs_path())

    def move(self, destination):
        """Called to move a resource to a new location. Overwrite is assumed, the DAV server
        will refuse to move to an existing resource otherwise. This method needs to gracefully
        handle a pre-existing destination of any type."""
        if destination.exists():
            destination.delete()
        if self.isdir():
            destination.mkdir()
            for child in self.get_children():
                child.move(self.__class__(self.server, safe_join(destination.path, child.get_name())))
            self.delete()
        else:
            os.rename(self.get_abs_path(), destination.get_abs_path())

    def get_etag(self):
        """Calculate an etag for this resource. The default implementation uses an md5 sub of the
        absolute path modified time and size. Can be overridden if resources are not stored in a
        file system. The etag is used to detect changes to a resource between HTTP calls. So this
        needs to change if a resource is modified."""
        hashsum = hashlib.md5()
        hashsum.update(self.get_abs_path().encode('utf-8'))
        hashsum.update(str(self.get_mtime_stamp()))
        hashsum.update(str(self.get_size()))
        return hashsum.hexdigest()


class DummyReadFSDavResource(BaseFSDavResource):
    def read(self):
        return file(self.get_abs_path(), 'r').read()


class DummyWriteFSDavResource(BaseFSDavResource):
    def write(self, content):
        with file(self.get_abs_path(), 'w') as f:
            shutil.copyfileobj(content, f)


class DummyFSDAVResource(DummyReadFSDavResource, DummyWriteFSDavResource, BaseFSDavResource):
    pass


class SendFileFSDavResource(BaseFSDavResource):
    quote = False

    def read(self):
        response = HttpResponse()
        full_path = self.get_abs_path().encode('utf-8')
        if self.quote:
            full_path = urllib.quote(full_path)
        response['X-SendFile'] = full_path
        response['Content-Type'] = mimetypes.guess_type(self.get_name())
        response['Content-Length'] = self.get_size()
        response['Last-Modified'] = http_date(self.get_mtime_stamp())
        response['ETag'] = self.get_etag()
        raise ResponseException(response)


class RedirectFSDavResource(BaseFSDavResource):
    prefix = "/"

    def read(self):
        response = HttpResponse()
        response['X-Accel-Redirect'] = url_join(self.prefix, self.get_path().path.encode('utf-8'))
        response['X-Accel-Charset'] = 'utf-8'
        response['Content-Type'] = mimetypes.guess_type(self.get_name())
        response['Content-Length'] = self.get_size()
        response['Last-Modified'] = http_date(self.get_mtime_stamp())
        response['ETag'] = self.get_etag()

        raise ResponseException(response)
