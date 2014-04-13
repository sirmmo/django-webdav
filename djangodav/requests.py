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


class DavRequest(object):
    """Wraps a Django request object, and extends it with some WebDAV
    specific methods."""
    def __init__(self, server, request, path):
        self.server = server
        self.request = request
        self.path = path

    def __getattr__(self, name):
        return getattr(self.request, name)

    def get_base(self):
        """Assuming the view is configured via urls.py to pass the path portion using
        a regular expression, we can subtract the provided path from the full request
        path to determine our base. This base is what we can make all absolute URLs
        from."""
        return self.META['PATH_INFO'][:-len(self.path)]

    def get_base_url(self):
        """Build a base URL for our request. Uses the base path provided by get_base()
        and the scheme/host etc. in the request to build a URL that can be used to
        build absolute URLs for WebDAV resources."""
        return self.build_absolute_uri(self.get_base())
