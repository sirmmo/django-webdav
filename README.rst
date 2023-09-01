DjangoDav
=========

Production ready WebDav extension for Django.

.. image:: https://travis-ci.org/meteozond/djangodav.svg

Motivation
----------

Django is a very popular tool which provides data representation and management. One of the key goals is to provide
machine access to it. Most popular production ready tools provide json based api access. Which have their own
advantages and disadvantages.

WebDav today is a standard for cooperative document management. Its clients are built in the modern operation systems
and supported by the world popular services. But it very important to remember that it's not only about file storage,
WebDab provides a set of methods to deal with tree structured objects of any kind.

Providing WebDav access to Django resources opens new horizons for building Web2.0 apps, with inplace edition and
providing native operation system access to the stored objects.


Difference with SmartFile django-webdav
---------------------------------------

Base resource functionality was separated into BaseResource class from the storage
functionality which developers free to choose from provided or implement themselves.

Improved class dependencies. Resource class don’t know anything about url or server, its
goal is only to store content and provide proper access.

Removed properties helper class. View is now responsible for xml generation, and resource
provides actual property list.

Server is now inherited from Django Class Based View, and renamed to DavView.

Key methods covered with tests.

Removed redundant request handler.

Added FSResource and DBResource to provide file system and data base access.

Xml library usage is replaced with lxml to achieve proper xml generation code readability.


How to create simple filesystem webdav resource
-----------------------------------------------

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

    from djangodav.acls import FullAcl
    from djangodav.locks import DummyLock
    from djangodav.views import DavView

    from django.conf.urls import patterns

    from .resource import MyDavResource

    urlpatterns = patterns('',
        (r'^fsdav(?P<path>.*)$', DavView.as_view(resource_class=MyDavResource, lock_class=DummyLock,
         acl_class=FullAcl)),
    )
