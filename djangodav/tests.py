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
from django.http import HttpRequest
from django.test import TestCase
from djangodav.base.resource import BaseDavResource
from djangodav.fs.resource import BaseFSDavResource
from mock import patch, Mock


class MyDavResource(BaseDavResource):
    base_url = 'http://testserver/base/'


class TestBaseDavResource(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.resource = MyDavResource(self.request, "/path/to/name")

    def test_path(self):
        self.assertEqual(self.resource.path, ['path', 'to', 'name'])

    @patch('djangodav.base.resource.BaseDavResource.isdir', Mock(return_value=True))
    def test_get_path_collection(self):
        self.assertEqual(self.resource.get_path(), 'path/to/name/')

    @patch('djangodav.base.resource.BaseDavResource.isdir', Mock(return_value=False))
    def test_get_path_object(self):
        self.assertEqual(self.resource.get_path(), 'path/to/name')

    @patch('djangodav.base.resource.BaseDavResource.isdir', Mock(return_value=True))
    def test_get_url_folder(self):
        self.assertEqual(self.resource.get_url(), 'http://testserver/base/path/to/name/')

    @patch('djangodav.base.resource.BaseDavResource.get_children', Mock(return_value=[]))
    def test_get_descendants(self):
        self.assertEqual(list(self.resource.get_descendants(depth=1, include_self=True)), [self.resource])

    def test_get_dirname(self):
        self.assertEqual(self.resource.get_dirname(), '/path/to/')

    def test_get_name(self):
        self.assertEqual(self.resource.get_name(), 'name')


class MyFSDavResource(BaseFSDavResource):
    base_url = 'http://testserver/base/'
    root = '/some/folder/'


class TestFSDavResource(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.resource = MyFSDavResource(self.request, "/path/to/name")

    @patch('djangodav.fs.resource.os.path.isdir')
    def test_isdir(self, isdir):
        isdir.return_value = True
        self.assertTrue(self.resource.isdir())
        isdir.assert_called_with('/some/folder/path/to/name')

    @patch('djangodav.fs.resource.os.path.isfile')
    def test_isfile(self, isfile):
        isfile.return_value = True
        self.assertTrue(self.resource.isfile())
        isfile.assert_called_with('/some/folder/path/to/name')

    @patch('djangodav.fs.resource.os.path.exists')
    def test_isfile(self, exists):
        exists.return_value = True
        self.assertTrue(self.resource.exists())
        exists.assert_called_with('/some/folder/path/to/name')

    @patch('djangodav.fs.resource.os.path.getsize')
    def test_get_size(self, getsize):
        getsize.return_value = 42
        self.assertEquals(self.resource.get_size(), 42)
        getsize.assert_called_with('/some/folder/path/to/name')

    def test_get_abs_path(self):
        self.assertEquals(self.resource.get_abs_path(), '/some/folder/path/to/name')

    @patch('djangodav.fs.resource.os.listdir')
    def test_get_children(self, listdir):
        listdir.return_value=[]
        self.assertEqual(list(self.resource.get_children()), [])
        listdir.assert_called_with('/some/folder/path/to/name')
