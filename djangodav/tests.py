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
from djangodav.base.server import BaseDavServer
from djangodav.fs.resource import FSDavResource
from djangodav.fs.server import FSDavServer
from mock import patch, Mock


class MyFSDavServer(FSDavServer):
    root = '/tmp/'


class TestBaseDavResource(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.META['PATH_INFO'] = '/base/path/'
        self.request.META['SERVER_NAME'] = 'testserver'
        self.request.META['SERVER_PORT'] = 80
        self.server = BaseDavServer(self.request, "/path/")
        self.resource = BaseDavResource(self.server, "/path/")

    def test_get_url_file(self):
        BaseDavResource.isdir = Mock(return_value=True)
        BaseDavResource.isfile = Mock(return_value=False)
        self.assertEqual(self.resource.get_url(), 'http://testserver/base/path/')

    def test_get_url_folder(self):
        BaseDavResource.isdir = Mock(return_value=False)
        BaseDavResource.isfile = Mock(return_value=True)
        self.assertEqual(self.resource.get_url(), 'http://testserver/base/path')


class TestFSDavResource(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.server = MyFSDavServer(self.request, "/path/")
        self.resource = FSDavResource(self.server, "/path/")

    @patch('djangodav.fs.resource.os.path.isdir')
    def test_isdir(self, isdir):
        isdir.return_value = True
        self.assertTrue(self.resource.isdir())
        isdir.assert_called_with('/tmp/path')

    @patch('djangodav.fs.resource.os.path.isfile')
    def test_isfile(self, isfile):
        isfile.return_value = True
        self.assertTrue(self.resource.isfile())
        isfile.assert_called_with('/tmp/path')

    @patch('djangodav.fs.resource.os.path.exists')
    def test_isfile(self, exists):
        exists.return_value = True
        self.assertTrue(self.resource.exists())
        exists.assert_called_with('/tmp/path')

    @patch('djangodav.fs.resource.os.path.basename')
    def test_get_name(self, basename):
        basename.return_value = 'path'
        self.assertEquals(self.resource.get_name(), 'path')
        basename.assert_called_with('/path')

    @patch('djangodav.fs.resource.os.path.getsize')
    def test_get_size(self, getsize):
        getsize.return_value = 42
        self.assertEquals(self.resource.get_size(), 42)
        getsize.assert_called_with('/tmp/path')
