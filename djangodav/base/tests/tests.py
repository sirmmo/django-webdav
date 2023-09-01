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
from djangodav.base.resources import BaseDavResource
from djangodav.base.tests.resources import MockCollection, MockObject, MissingMockCollection
from mock import patch, Mock


class TestBaseDavResource(TestCase):

    def setUp(self):
        self.resource = BaseDavResource("/path/to/name")

    def test_path(self):
        self.assertEqual(self.resource.path, ['path', 'to', 'name'])

    @patch('djangodav.base.resources.BaseDavResource.is_collection', True)
    def test_get_path_collection(self):
        self.assertEqual(self.resource.get_path(), '/path/to/name/')

    @patch('djangodav.base.resources.BaseDavResource.is_collection', False)
    def test_get_path_object(self):
        self.assertEqual(self.resource.get_path(), '/path/to/name')

    @patch('djangodav.base.resources.BaseDavResource.get_children', Mock(return_value=[]))
    def test_get_descendants(self):
        self.assertEqual(list(self.resource.get_descendants(depth=1, include_self=True)), [self.resource])

    def test_get_parent_path(self):
        self.assertEqual(self.resource.get_parent_path(), '/path/to/')

    def test_displayname(self):
        self.assertEqual(self.resource.displayname, 'name')

    def test_move_collection(self):
        child = MockObject('/path/to/src/child', move=Mock())
        src = MockCollection('/path/to/src/', get_children=Mock(return_value=[child]), delete=Mock())
        dst = MissingMockCollection('/path/to/dst/', create_collection=Mock())

        src.move(dst)

        src.delete.assert_called_with()
        dst.create_collection.assert_called_with()
        self.assertEqual(child.move.call_args[0][0].path, ['path', 'to', 'dst', 'child'])

    def test_move_collection_collision(self):
        child = MockObject('/path/to/src/child', move=Mock())
        src = MockCollection('/path/to/src/', get_children=Mock(return_value=[child]), delete=Mock())
        dst = MockCollection('/path/to/dst/', create_collection=Mock())

        src.move(dst)

        src.delete.assert_called_with()
        self.assertEqual(dst.create_collection.call_count, 0)
        self.assertEqual(child.move.call_args[0][0].path, ['path', 'to', 'dst', 'child'])

    def test_copy_collection(self):
        child = MockObject('/path/to/src/child', copy=Mock())
        src = MockCollection('/path/to/src/', get_children=Mock(return_value=[child]), delete=Mock())
        dst = MissingMockCollection('/path/to/dst/', create_collection=Mock())

        src.copy(dst)

        dst.create_collection.assert_called_with()
        self.assertEqual(child.copy.call_args[0][0].path, ['path', 'to', 'dst', 'child'])

    def test_copy_collection_collision(self):
        child = MockObject('/path/to/src/child', copy=Mock())
        src = MockCollection('/path/to/src/', get_children=Mock(return_value=[child]), delete=Mock())
        dst = MockCollection('/path/to/dst/', create_collection=Mock())

        src.copy_collection(dst)

        self.assertEqual(dst.create_collection.call_count, 0)
        self.assertEqual(child.copy.call_args[0][0].path, ['path', 'to', 'dst', 'child'])

    def test_copy_collection_depth_0(self):
        child = MockObject('/path/to/src/child', copy=Mock())
        src = MockCollection('/path/to/src/', get_children=Mock(return_value=[child]), delete=Mock())
        dst = MissingMockCollection('/path/to/dst/', create_collection=Mock())

        src.copy(dst, 0)

        dst.create_collection.assert_called_with()
        self.assertEqual(child.copy.call_count, 0)
