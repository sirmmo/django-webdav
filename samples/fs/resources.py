from django.conf import settings
from djangodav.base.resources import MetaEtagMixIn
from djangodav.fs.resources import DummyFSDAVResource


class TempDirWebDavResource(MetaEtagMixIn, DummyFSDAVResource):
    root = settings.WEBDAV_ROOT
