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
from sys import getfilesystemencoding
import os
import datetime
import shutil
import urllib

from django.http import HttpResponse
from django.utils.http import http_date
from django.utils.feedgenerator import rfc3339_date

from djangodav.base.resource import BaseDavResource
from djangodav.response import ResponseException
from djangodav.utils import safe_join, url_join


fs_encoding = getfilesystemencoding()


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

    @property
    def getcontentlength(self):
        """Return the size of the resource in bytes."""
        return os.path.getsize(self.get_abs_path())

    @property
    def creationdate(self):
        """Return the create time as rfc3339_date."""
        return rfc3339_date(self.get_ctime())

    @property
    def getlastmodified(self):
        """Return the modified time as http_date."""
        return http_date(os.stat(self.get_abs_path()).st_ctime)

    def get_ctime(self):
        """Return the create time as datetime object."""
        return datetime.datetime.fromtimestamp(os.stat(self.get_abs_path()).st_ctime)

    def get_mtime(self):
        """Return the modified time as datetime object."""
        return datetime.datetime.fromtimestamp(os.stat(self.get_abs_path()).st_mtime)

    @property
    def getetag(self):
        """Calculate an etag for this resource. The default implementation uses an md5 sub of the
        absolute path modified time and size. Can be overridden if resources are not stored in a
        file system. The etag is used to detect changes to a resource between HTTP calls. So this
        needs to change if a resource is modified."""
        hashsum = hashlib.md5()
        hashsum.update(self.get_abs_path().encode('utf-8'))
        hashsum.update(str(self.get_mtime()))
        hashsum.update(str(self.get_ctime()))
        hashsum.update(str(self.getcontentlength))
        return hashsum.hexdigest()

    def is_collection(self):
        """Return True if this resource is a directory (collection in WebDAV parlance)."""
        return os.path.isdir(self.get_abs_path())

    def is_object(self):
        """Return True if this resource is a file (resource in WebDAV parlance)."""
        return os.path.isfile(self.get_abs_path())

    def exists(self):
        """Return True if this resource exists."""
        return os.path.exists(self.get_abs_path())

    def get_children(self):
        """Return an iterator of all direct children of this resource."""
        for child in os.listdir(self.get_abs_path()):
            if not isinstance(child, unicode):
                child = child.decode(fs_encoding)
            yield self.__class__(url_join(*(self.path + [child])))

    def write(self, content):
        raise NotImplemented

    def read(self):
        raise NotImplemented

    def delete(self):
        """Delete the resource, recursive is implied."""
        if self.is_collection():
            for child in self.get_children():
                child.delete()
            os.rmdir(self.get_abs_path())
        elif self.is_object():
            os.remove(self.get_abs_path())

    def create_collection(self):
        """Create a directory in the location of this resource."""
        os.mkdir(self.get_abs_path())

    def copy(self, destination, depth=0):
        """Called to copy a resource to a new location. Overwrite is assumed, the DAV server
        will refuse to copy to an existing resource otherwise. This method needs to gracefully
        handle a pre-existing destination of any type. It also needs to respect the depth
        parameter. depth == -1 is infinity."""
        if self.is_collection():
            if destination.is_object():
                destination.delete()
            if not destination.is_collection():
                destination.create_collection()
            # If depth is less than 0, then it started out as -1.
            # We need to keep recursing until we hit 0, or forever
            # in case of infinity.
            if depth != 0:
                for child in self.get_children():
                    child.copy(self.__class__(safe_join(destination.path, child.displayname)),
                               depth=depth-1)
        else:
            if destination.is_collection():
                destination.delete()
            shutil.copy(self.get_abs_path(), destination.get_abs_path())

    def move(self, destination):
        """Called to move a resource to a new location. Overwrite is assumed, the DAV server
        will refuse to move to an existing resource otherwise. This method needs to gracefully
        handle a pre-existing destination of any type."""
        if destination.exists():
            destination.delete()
        if self.is_collection():
            destination.create_collection()
            for child in self.get_children():
                child.move(self.__class__(safe_join(destination.path, child.displayname)))
            self.delete()
        else:
            os.rename(self.get_abs_path(), destination.get_abs_path())

class DummyReadFSDavResource(BaseFSDavResource):
    def read(self):
        f = open(self.get_abs_path(), 'r')
        resp = f.read()
        f.close()
        return resp


class DummyWriteFSDavResource(BaseFSDavResource):
    def write(self, content):
        f = open(self.get_abs_path(), 'w')
        f.write(content)
        f.close()


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
        response['Content-Type'] = mimetypes.guess_type(self.displayname)
        response['Content-Length'] = self.getcontentlength
        response['Last-Modified'] = http_date(self.getlastmodified)
        response['ETag'] = self.getetag
        raise ResponseException(response)


class RedirectFSDavResource(BaseFSDavResource):
    prefix = "/"

    def read(self):
        response = HttpResponse()
        response['X-Accel-Redirect'] = url_join(self.prefix, self.get_path().path.encode('utf-8'))
        response['X-Accel-Charset'] = 'utf-8'
        response['Content-Type'] = mimetypes.guess_type(self.displayname)
        response['Content-Length'] = self.getcontentlength
        response['Last-Modified'] = http_date(self.getlastmodified)
        response['ETag'] = self.getetag
        raise ResponseException(response)
