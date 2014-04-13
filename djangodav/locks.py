from django.utils import synch


class DavLock(object):
    def __init__(self, server):
        self.server = server
        self.lock = synch.RWLock()

    def get(self, res):
        """Gets all active locks for the requested resource. Returns a list of locks."""
        self.lock.reader_enters()
        try:
            pass
        finally:
            self.lock.reader_leaves()

    def acquire(self, res, type, scope, depth, owner, timeout):
        """Creates a new lock for the given resource."""
        self.lock.writer_enters()
        try:
            pass
        finally:
            self.lock.writer_leaves()

    def release(self, lock):
        """Releases the lock referenced by the given lock id."""
        self.lock.writer_enters()
        try:
            pass
        finally:
            self.lock.writer_leaves()

    def del_locks(self, res):
        """Releases all locks for the given resource."""
        self.lock.writer_enters()
        try:
            pass
        finally:
            self.lock.writer_leaves()
