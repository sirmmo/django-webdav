======
How to
======

Create simple filesystem webdav resource
----------------------------------------

1. Create resource.py
~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from django.conf import settings
    from djangodav.base.resources import MetaEtagMixIn
    from djangodav.fs.resources import DummyFSDAVResource

    class MyDavResource(MetaEtagMixIn, DummyFSDAVResource):
        root = '/path/to/folder'


2. Register WebDav view in urls.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from djangodav.acl import FullAcl
    from djangodav.lock import DummyLock
    from djangodav.views import DavView

    from django.conf.urls import patterns

    from .resource import TempDirWebDavResource

    urlpatterns = patterns('',
        (r'^fsdav(?P<path>.*)$', DavView.as_view(resource_class=MyDavResource, lock_class=DummyLock,
         acl_class=FullAcl)),
    )


Create simple database webdav resource
--------------------------------------

1. Create models.py
~~~~~~~~~~~~~~~~~~~

.. code:: python

    from django.db import models
    from django.utils.timezone import now

    class BaseDavModel(models.Model):
        name = models.CharField(max_length=255)
        created = models.DateTimeField(default=now)
        modified = models.DateTimeField(default=now)

        class Meta:
            abstract = True


    class CollectionModel(BaseDavModel):
        parent = models.ForeignKey('self', blank=True, null=True)
        size = 0

        class Meta:
            unique_together = (('parent', 'name'),)


    class ObjectModel(BaseDavModel):
        parent = models.ForeignKey(CollectionModel, blank=True, null=True)
        size = models.IntegerField(default=0)
        content = models.TextField(default=u"")
        md5 = models.CharField(max_length=255)

        class Meta:
            unique_together = (('parent', 'name'),)

2. Create resource.py
~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from base64 import b64encode, b64decode
    from hashlib import md5

    from django.utils.timezone import now
    from djangodav.db.resources import NameLookupDBDavMixIn, BaseDBDavResource
    from samples.db.models import CollectionModel, ObjectModel

    class MyDBDavResource(NameLookupDBDavMixIn, BaseDBDavResource):
        collection_model = CollectionModel
        object_model = ObjectModel

        def write(self, content):
            size = len(content)
            hashsum = md5(content).hexdigest()
            content = b64encode(content)
            if not self.exists:
                self.object_model.objects.create(
                    name=self.displayname,
                    parent=self.get_parent().obj,
                    md5=hashsum,
                    size=size,
                    content=content
                )
                return
            self.obj.size = size
            self.obj.modified = now()
            self.obj.content = content
            self.md5 = hashsum
            self.obj.save(update_fields=['content', 'size', 'modified', 'md5'])

        def read(self):
            return b64decode(self.obj.content)

        @property
        def getetag(self):
            return self.obj.md5

        @property
        def getcontentlength(self):
            return self.obj.size

2. Register DavView in urls.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from djangodav.acls import FullAcl
    from djangodav.locks import DummyLock

    from djangodav.views import DavView

    from django.conf.urls import patterns
    from samples.db.resource import MyDBDavResource


    urlpatterns = patterns('',
        # Mirroring tmp folder
        (r'^dbdav(?P<path>.*)$', DavView.as_view(resource_class=MyDBDavResource, lock_class=DummyLock, acl_class=FullAcl)),
    )
