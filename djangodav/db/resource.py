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
from operator import and_
from django.db.models import Q
from django.utils.functional import cached_property
from djangodav.base.resource import BaseDavResource
from djangodav.utils import url_join


class BaseDBDavResource(BaseDavResource):
    __is_object = False
    __exists = False

    collection_model = None
    object_model = None

    collection_attribute = 'parent'
    created_attribute = 'created'
    modified_attribute = 'modified'
    name_attribute = 'name'
    size_attribute = 'size'

    def __init__(self, path, **kwargs):
        if 'obj' in kwargs:  # Accepting ready object to reduce db requests
            self.__dict__['obj'] = kwargs.pop('obj')
            self.__exists = True
            if isinstance(self.obj, self.object_model):
                self.__is_object = True
        super(BaseDBDavResource, self).__init__(path)
        if not self.path:
            self.__exists = True

    @cached_property
    def obj(self):
        raise NotImplemented()

    @property
    def getcontentlength(self):
        return getattr(self.obj, self.size_attribute)

    @property
    def creationdate(self):
        return getattr(self.obj, self.created_attribute)

    @property
    def getlastmodified(self):
        return getattr(self.obj, self.modified_attribute)

    def is_collection(self):
        return self.__exists and not self.__is_object

    def is_object(self):
        return self.__exists and self.__is_object

    def exists(self):
        return self.__exists

    def get_children(self):
        """Return an iterator of all direct children of this resource."""
        if self.__exists and not self.obj is None and isinstance(self.obj, self.object_model):
            return

        for model in [self.collection_model, self.object_model]:
            for child in model.objects.filter(**{self.collection_attribute: self.obj}):
                yield self.__class__(
                    url_join(*(self.path + [child.name])),
                    obj=child    # Sending ready object to reduce db requests
                )

    def read(self):
        raise NotImplemented

    def write(self, content):
        raise NotImplemented

    def delete(self):
        if not self.obj:
            return
        self.obj.delete()

    def create_collection(self):
        """Create a directory in the location of this resource."""
        if hasattr(self, 'obj'):
            raise Exception('exists')
        name = self.path[-1]
        parent = self.__class__("/".join(self.path[:-1])).obj
        self.collection_model.objects.create(**{self.collection_attribute: parent, 'name': name})

    def copy(self, destination, depth=0):
        """Called to copy a resource to a new location. Overwrite is assumed, the DAV server
        will refuse to copy to an existing resource otherwise. This method needs to gracefully
        handle a pre-existing destination of any type. It also needs to respect the depth
        parameter. depth == -1 is infinity."""
        raise NotImplemented()

    def move(self, destination):
        """Called to move a resource to a new location. Overwrite is assumed, the DAV server
        will refuse to move to an existing resource otherwise. This method needs to gracefully
        handle a pre-existing destination of any type."""
        name = destination.path_lst[-1]
        path = destination.path_lst[:-1]
        parent = self.collection_model.objects.get_by_path(*path)
        self.obj.move({self.collection_attribute: parent, 'name': name})


class NameLookupDBDavResource(BaseDBDavResource):
    """Object lookup by joining collections tables to fit given path"""

    @cached_property
    def obj(self):
        if not self.path:
            self.__exists = True
            return

        try:
            obj = self.get_model_by_path(self.collection_model, *self.path)
            self.__exists = True
            return obj
        except self.collection_model.DoesNotExist:
            name = self.path[-1]
            parent = self.get_model_by_path(self.collection_model, *self.path[:-1])
            try:
                qs = self.object_model.objects.select_related(self.collection_attribute)
                obj = qs.get({self.collection_attribute: parent, 'name': name})
                self.__exists = True
                self.__is_object = True
                return obj
            except self.object_model.DoesNotExist:
                pass

    def get_model_by_path(self, model, *path):
        if not path:
            return None

        args = []
        i = 0
        for part in reversed(path):
            args.append(Q(**{"__".join(([self.collection_attribute] * i) + [self.name_attribute]): part}))
            i += 1
        args.append(Q(**{"__".join([self.collection_attribute] * len(path)): None}))
        related = ["__".join([self.collection_attribute] * i) for i in range(1, len(path))]

        qs = model.objects
        if related:
            qs = qs.select_related(*related)
        try:
            return qs.filter(reduce(and_, args))[0]
        except IndexError:
            raise model.DoesNotExist()
