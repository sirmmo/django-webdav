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


class BaseLock(object):
    def __init__(self, resource):
        self.resource = resource

    def get(self):
        """Gets all active locks for the requested resource. Returns a list of locks."""
        raise NotImplementedError()

    def acquire(self, lockscope, locktype, depth, timeout, owner):
        """Creates a new lock for the given resource."""
        raise NotImplementedError()

    def release(self, token):
        """Releases the lock referenced by the given lock id."""
        raise NotImplementedError()

    def del_locks(self):
        """Releases all locks for the given resource."""
        raise NotImplementedError()
