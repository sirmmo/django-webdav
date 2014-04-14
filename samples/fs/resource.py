import tempfile
from djangodav.fs.resource import DummyFSDAVResource


class TempDirWebDavResource(DummyFSDAVResource):
    root = tempfile.gettempdir()
