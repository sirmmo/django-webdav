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
from django.test import TestCase
from djangodav.base.resource import BaseDavResource
from mock import patch, Mock


class TestBaseDavResource(TestCase):

    def setUp(self):
        self.resource = BaseDavResource("/path/to/name")

    def test_path(self):
        self.assertEqual(self.resource.path, ['path', 'to', 'name'])

    @patch('djangodav.base.resource.BaseDavResource.is_collection', True)
    def test_get_path_collection(self):
        self.assertEqual(self.resource.get_path(), '/path/to/name/')

    @patch('djangodav.base.resource.BaseDavResource.is_collection', False)
    def test_get_path_object(self):
        self.assertEqual(self.resource.get_path(), '/path/to/name')

    @patch('djangodav.base.resource.BaseDavResource.get_children', Mock(return_value=[]))
    def test_get_descendants(self):
        self.assertEqual(list(self.resource.get_descendants(depth=1, include_self=True)), [self.resource])

    def test_get_parent_path(self):
        self.assertEqual(self.resource.get_parent_path(), '/path/to/')

    def test_displayname(self):
        self.assertEqual(self.resource.displayname, 'name')
