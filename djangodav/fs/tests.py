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
from djangodav.fs.resources import BaseFSDavResource
from mock import patch


class TestFSDavResource(TestCase):
    class FSDavResource(BaseFSDavResource):
        base_url = 'http://testserver/base/'
        root = '/some/folder/'

    def setUp(self):
        self.resource = self.FSDavResource("/path/to/name")

    @patch('djangodav.fs.resources.os.path.isdir')
    def test_is_collection(self, isdir):
        isdir.return_value = True
        self.assertTrue(self.resource.is_collection)
        isdir.assert_called_with('/some/folder/path/to/name')

    @patch('djangodav.fs.resources.os.path.isfile')
    def test_isfile(self, isfile):
        isfile.return_value = True
        self.assertTrue(self.resource.is_object)
        isfile.assert_called_with('/some/folder/path/to/name')

    @patch('djangodav.fs.resources.os.path.exists')
    def test_isfile(self, exists):
        exists.return_value = True
        self.assertTrue(self.resource.exists)
        exists.assert_called_with('/some/folder/path/to/name')

    @patch('djangodav.fs.resources.os.path.getsize')
    def test_get_size(self, getsize):
        getsize.return_value = 42
        self.assertEquals(self.resource.getcontentlength, 42)
        getsize.assert_called_with('/some/folder/path/to/name')

    def test_get_abs_path(self):
        self.assertEquals(self.resource.get_abs_path(), '/some/folder/path/to/name')

    @patch('djangodav.fs.resources.os.path.isdir')
    @patch('djangodav.fs.resources.os.listdir')
    def test_get_children(self, listdir, isdir):
        listdir.return_value=['child1', 'child2']
        children = list(self.resource.get_children())
        self.assertEqual(children[0].path, ['path', 'to', 'name', 'child1'])
        self.assertEqual(children[1].path, ['path', 'to', 'name', 'child2'])
        listdir.assert_called_with('/some/folder/path/to/name')
