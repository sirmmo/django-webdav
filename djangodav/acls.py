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


class DavAcl(object):
    """Represents all the permissions that a user might have on a resource. This
    makes it easy to implement virtual permissions."""
    def __init__(self, read=False, write=False, delete=False, full=None):
        if full is not None:
            self.read = self.write = self.delete = \
                self.create = self.relocate = full
        self.read = read
        self.write = write
        self.delete = delete


class ReadOnlyAcl(DavAcl):
    def __init__(self, read=True, write=False, delete=False, full=None):
        super(ReadOnlyAcl, self).__init__(read, write, delete, full)


class FullAcl(DavAcl):
    def __init__(self, read=True, write=True, delete=True, full=None):
        super(FullAcl, self).__init__(read, write, delete, full)
