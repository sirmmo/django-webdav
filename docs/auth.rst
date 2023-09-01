==============
Authentication
==============

Introduction
------------

WebDav like any other http api protocol accepts wide range of authentication methods: Basic, Digest, OAuth, OAuth2, etc.
Most of them are already developed in the api other libraries. So we provide mixins you can use to bring in Django Rest
Framework or Tastipie authentication layer support.


Using Django REST framework authentication
------------------------------------------

Inherit your DavView from `RestAuthViewMixIn` and provide REST authentication instances as `authentications` property
tuple.

..code: python

    from rest_framework.authentication import SessionAuthentication, BasicAuthentication
    from djangodav.views import DavView

    class AuthFsDavView(RestAuthViewMixIn, DavView):
        authentications = (BasicAuthentication(), SessionAuthentication())


Using Django Tastypie authentication
------------------------------------

Inherit your DavView from `TastypieAuthViewMixIn` and provide Tastpie authentication instance as `authentication`
property tuple.

..code: python

    from djangodav.auth.tasty import TastypieAuthViewMixIn
    from tastypie.authentication import BasicAuthentication


    class RestAuthDavView(TastypieAuthViewMixIn, DavView):
        authentication = BasicAuthentication()

        resource_class = TempDirWebDavResource
        lock_class = DummyLock
        acl_class = FullAcl

With Tastipie you can also use `MultiAuthentication` to provide several authentication methods.

..code: python

    from djangodav.auth.tasty import TastypieAuthViewMixIn
    from tastypie.authentication import BasicAuthentication, MultiAuthentication, SessionAuthentication


    class TastyAuthDavView(TastypieAuthViewMixIn, DavView):
        authentication = MultiAuthentication(BasicAuthentication(), SessionAuthentication())

        resource_class = TempDirWebDavResource
        lock_class = DummyLock
        acl_class = FullAcl
