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
from lxml.etree import ElementTree
from lxml import etree

from djangodav.base.tests.resource import MockCollection, MockObject, MissingMockCollection
from djangodav.fs.tests import *
from djangodav.utils import D, WEBDAV_NSMAP
from djangodav.views import WebDavView
from mock import Mock


class TestView(TestCase):
    def setUp(self):
        self.blank_collection = MockCollection(
            path='/blank_collection/',
            get_descendants=Mock(return_value=[])
        )
        self.sub_object = MockObject(
            path='/collection/sub_object',
            getcontentlength=42,
            get_descendants=Mock(return_value=[])
        )
        self.sub_collection = MockCollection(
            path='/collection/sub_colection/',
            get_descendants=Mock(return_value=[])
        )
        self.top_collection = MockCollection(
            path='/collection/',
            get_descendants=Mock(return_value=[self.sub_object, self.sub_collection])
        )

    def test_get_collection_redirect(self):
        actual_path = '/collection/'
        wrong_path = '/collection'
        v = WebDavView(path=wrong_path)
        v.__dict__['resource'] = MockCollection(actual_path)
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value=wrong_path))
        resp = v.get(request, wrong_path, 'xbody')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(actual_path, resp['Location'])

    def test_get_object_redirect(self):
        actual_path = '/object.mp4'
        wrong_path = '/object.mp4/'
        r = WebDavView(path=wrong_path)
        r.__dict__['resource'] = MockObject(actual_path)
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value=wrong_path))
        resp = r.get(request, wrong_path, 'xbody')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], actual_path)

    def test_missing(self):
        path = '/object.mp4'
        r = WebDavView(path=path)
        r.__dict__['resource'] = MissingMockCollection(path)
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value=path))
        resp = r.get(request, path, 'xbody')
        self.assertEqual(resp.status_code, 404)

    def test_propfind_listing(self):
        self.top_collection.get_descendants.return_value += [self.top_collection]
        request = Mock(META={})
        path = '/collection/'
        v = WebDavView(base_url='/base/', path=path, request=request)
        v.__dict__['resource'] = self.top_collection
        resp = v.propfind(request, path, None)
        self.assertEqual(resp.status_code, 207)
        self.assertEqual(resp.content,
            etree.tostring(D.multistatus(
                D.response(
                    D.href('/base/collection/sub_object'),
                    D.propstat(
                        D.prop(
                            D.getcontentlength("42"),
                            D.creationdate("1983-12-23T23:00:00Z"),
                            D.getlastmodified("Wed, 24 Dec 2014 06:00:00 GMT"),
                            D.resourcetype(),
                            D.displayname("sub_object"),
                        ),
                        D.status("HTTP/1.1 200 OK")
                    )
                ),
                D.response(
                    D.href('/base/collection/sub_colection/'),
                    D.propstat(
                        D.prop(
                            D.getcontentlength("0"),
                            D.creationdate("1983-12-23T23:00:00Z"),
                            D.getlastmodified("Wed, 24 Dec 2014 06:00:00 GMT"),
                            D.resourcetype(D.collection()),
                            D.displayname("sub_colection"),
                        ),
                        D.status("HTTP/1.1 200 OK")
                    )
                ),
                D.response(
                    D.href('/base/collection/'),
                    D.propstat(
                        D.prop(
                            D.getcontentlength("0"),
                            D.creationdate("1983-12-23T23:00:00Z"),
                            D.getlastmodified("Wed, 24 Dec 2014 06:00:00 GMT"),
                            D.resourcetype(D.collection()),
                            D.displayname("collection"),
                        ),
                        D.status("HTTP/1.1 200 OK")
                    )
                ),
            ), pretty_print=True)
        )
