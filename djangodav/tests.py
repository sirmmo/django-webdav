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


from djangodav.base.tests import *
from djangodav.fs.tests import *
from djangodav.utils import D, rfc1123_date, rfc3339_date
from djangodav.views import WebDavView


class TestView(TestCase):
    def setUp(self):
        class Resource(MagicMock):
            ALL_PROPS = BaseDavResource.ALL_PROPS
            getcontentlength = 0
            exists = True
            creationdate = rfc3339_date(now())
            getlastmodified = rfc1123_date(now())

        class Collection(Resource):
            is_collection = True
            is_object = False
            get_descendants=Mock(return_value=[])

        class Object(Resource):
            is_collection=False
            is_object=True

        self.Collection = Collection
        self.Object = Object

        self.blank_collection = Collection(
            displayname='blank_collection',
            get_path=Mock(return_value='/blank_collection/'),
            get_descendants=Mock(return_value=[])
        )
        self.sub_object = Object(
            getcontentlength=42,
            displayname='sub_object',
            get_path=Mock(return_value='/collection/sub_object/'),
            get_descendants=Mock(return_value=[])
        )
        self.sub_collection = Collection(
            displayname='sub_colection',
            get_path=Mock(return_value='/collection/sub_colection/'),
            get_descendants=Mock(return_value=[])
        )
        self.top_collection = Collection(
            displayname='collection',
            get_path=Mock(return_value='/collection/'),
            get_descendants=Mock(return_value=[self.sub_object, self.sub_collection])
        )

    def test_get_collection_redirect(self):
        v = WebDavView()
        v.__dict__['resource'] = self.Collection(displayname='collection')
        v.path = '/collection'
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value='/collection'))
        resp = v.get(request, '/collection', 'xbody')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/collection/')

    def test_get_object_redirect(self):
        r = WebDavView()
        r.__dict__['resource'] = self.Object(displayname='object.mp4')
        r.path = '/object.mp4/'
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value='/object.mp4/'))
        resp = r.get(request, '/object.mp4/', 'xbody')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/object.mp4')

    def test_not_exists(self):
        r = WebDavView()
        r.__dict__['resource'] = Mock(exists=False, is_collection=False, is_object=False, displayname='object.mp4')
        r.path = '/object.mp4/'
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value='/object.mp4/'))
        resp = r.get(request, '/object.mp4/', 'xbody')
        self.assertEqual(resp.status_code, 404)

    def test_propfind(self):
        request = Mock(META={})
        v = WebDavView(base_url='/bast/', path='/object.mp4/', request=request)
        v.__dict__['resource'] = self.top_collection
        v.request = request
        resp = v.propfind(request, '/colelction/', None)
        self.assertEqual(resp.status_code, 207)
