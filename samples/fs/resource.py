from django.conf import settings
from djangodav.base.resource import MetaEtagMixIn
from djangodav.fs.resource import DummyFSDAVResource


class TempDirWebDavResource(MetaEtagMixIn, DummyFSDAVResource):
    root = settings.WEBDAV_ROOT
