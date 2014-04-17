import tempfile
from djangodav.base.resource import MetaEtagMixIn
from djangodav.fs.resource import DummyFSDAVResource


class TempDirWebDavResource(MetaEtagMixIn, DummyFSDAVResource):
    root = tempfile.gettempdir()
