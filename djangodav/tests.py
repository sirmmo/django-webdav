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
from django.http import HttpResponse, HttpRequest
from djangodav.base.acl import FullAcl
from djangodav.response import ResponseException
from lxml import etree

from djangodav.base.tests.resource import MockCollection, MockObject, MissingMockCollection, MissingMockObject
from djangodav.fs.tests import *
from djangodav.utils import D, WEBDAV_NSMAP, rfc1123_date
from djangodav.views import WebDavView
from mock import Mock


class TestView(TestCase):
    def setUp(self):
        self.blank_collection = MockCollection(
            path='/blank_collection/',
            get_descendants=Mock(return_value=[]),
        )
        self.sub_object = MockObject(
            path='/collection/sub_object',
            getcontentlength=42,
            get_descendants=Mock(return_value=[]),
            get_parent=lambda: self.top_collection
        )
        self.missing_sub_object = MissingMockObject(
            path='/collection/missing_sub_object',
            getcontentlength=42,
            get_descendants=Mock(return_value=[]),
            get_parent=lambda: self.top_collection
        )
        self.sub_collection = MockCollection(
            path='/collection/sub_colection/',
            get_descendants=Mock(return_value=[]),
            get_parent=lambda: self.top_collection
        )
        self.top_collection = MockCollection(
            path='/collection/',
            get_descendants=Mock(return_value=[self.sub_object, self.sub_collection])
        )

    def test_get_collection_redirect(self):
        actual_path = '/collection/'
        wrong_path = '/collection'
        v = WebDavView(path=wrong_path, acl_class=FullAcl)
        v.__dict__['resource'] = MockCollection(actual_path)
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value=wrong_path))
        resp = v.get(request, wrong_path, 'xbody')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(actual_path, resp['Location'])

    def test_get_object_redirect(self):
        actual_path = '/object.mp4'
        wrong_path = '/object.mp4/'
        r = WebDavView(path=wrong_path, acl_class=FullAcl)
        r.__dict__['resource'] = MockObject(actual_path)
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value=wrong_path))
        resp = r.get(request, wrong_path, 'xbody')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], actual_path)

    def test_missing(self):
        path = '/object.mp4'
        r = WebDavView(path=path, acl_class=FullAcl)
        r.__dict__['resource'] = MissingMockCollection(path)
        request = Mock(META={'SERVERNANE': 'testserver'}, build_absolute_uri=Mock(return_value=path))
        resp = r.get(request, path, 'xbody')
        self.assertEqual(resp.status_code, 404)

    def test_propfind_listing(self):
        self.top_collection.get_descendants.return_value += [self.top_collection]
        request = Mock(META={})
        path = '/collection/'
        v = WebDavView(base_url='/base/', path=path, request=request, acl_class=FullAcl)
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

    def test_propfind_exact_names(self):
        self.sub_object.get_descendants.return_value += [self.sub_object]
        request = Mock(META={})
        path = 'collection/sub_object'
        v = WebDavView(base_url='/base/', path=path, request=request, acl_class=FullAcl)
        v.__dict__['resource'] = self.sub_object
        resp = v.propfind(request, path,
            etree.XPathDocumentEvaluator(ElementTree(
                D.propfind(
                    D.prop(
                        D.displayname(),
                        D.resourcetype(),
                    )
                )
            ), namespaces=WEBDAV_NSMAP)
        )
        self.assertEqual(resp.status_code, 207)
        self.assertEqual(resp.content,
            etree.tostring(D.multistatus(
                D.response(
                    D.href('/base/collection/sub_object'),
                    D.propstat(
                        D.prop(
                            D.displayname("sub_object"),
                            D.resourcetype(),
                        ),
                        D.status("HTTP/1.1 200 OK")
                    )
                ),
            ), pretty_print=True)
        )

    def test_propfind_allprop(self):
        self.sub_object.get_descendants.return_value += [self.sub_object]
        request = Mock(META={})
        path = 'collection/sub_object'
        v = WebDavView(base_url='/base/', path=path, request=request, acl_class=FullAcl)
        v.__dict__['resource'] = self.sub_object
        resp = v.propfind(request, path,
            etree.XPathDocumentEvaluator(ElementTree(
                D.propfind(
                    D.allprop()
                )
            ), namespaces=WEBDAV_NSMAP)
        )
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
            ), pretty_print=True)
        )


    def test_propfind_all_names(self):
        self.sub_object.get_descendants.return_value += [self.sub_object]
        request = Mock(META={})
        path = 'collection/sub_object'
        v = WebDavView(base_url='/base/', path=path, request=request, acl_class=FullAcl)
        v.__dict__['resource'] = self.sub_object
        resp = v.propfind(request, path,
            etree.XPathDocumentEvaluator(ElementTree(
                D.propfind(
                    D.propname()
                )
            ), namespaces=WEBDAV_NSMAP)
        )
        self.assertEqual(resp.status_code, 207)
        self.assertEqual(resp.content,
            etree.tostring(D.multistatus(
                D.response(
                    D.href('/base/collection/sub_object'),
                    D.propstat(
                        D.prop(
                            D.getcontentlength(),
                            D.creationdate(),
                            D.getlastmodified(),
                            D.resourcetype(),
                            D.displayname(),
                        ),
                        D.status("HTTP/1.1 200 OK")
                    )
                ),
            ), pretty_print=True)
        )

    def test_dispatch(self):
        request = Mock(
            spec=HttpRequest,
            META={
                'PATH_INFO': '/base/path/',
                'CONTENT_TYPE': 'text/xml',
                'CONTENT_LENGTH': '44'
            },
            method='GET',
            read=Mock(side_effect=[u"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n", u"<foo/>", u""])
        )
        v = WebDavView(request=request, get=Mock(return_value=HttpResponse()), _allowed_methods=Mock(return_value=['GET']))
        v.dispatch(request, '/path/')
        self.assertIsNotNone(v.xbody)
        self.assertEqual(v.base_url, '/base')
        self.assertEqual(v.path, '/path/')

    def test_allowed_object(self):
        v = WebDavView()
        v.__dict__['resource'] = self.sub_object
        self.assertEqual(v._allowed_methods(), ['OPTIONS', 'HEAD', 'GET', 'DELETE', 'PROPFIND', 'PROPPATCH', 'COPY', 'MOVE', 'LOCK', 'UNLOCK', 'PUT'])

    def test_allowed_collection(self):
        v = WebDavView()
        v.__dict__['resource'] = self.top_collection
        self.assertEqual(v._allowed_methods(), ['OPTIONS', 'HEAD', 'GET', 'DELETE', 'PROPFIND', 'PROPPATCH', 'COPY', 'MOVE', 'LOCK', 'UNLOCK'])

    def test_allowed_missing_collection(self):
        v = WebDavView()
        parent = MockCollection('/path/to/obj')
        v.__dict__['resource'] = MissingMockCollection('/path/', get_parent=Mock(return_value=parent))
        self.assertEqual(v._allowed_methods(), ['OPTIONS', 'PUT', 'MKCOL'])

    def test_allowed_missing_parent(self):
        v = WebDavView()
        parent = MissingMockCollection('/path/to/obj')
        v.__dict__['resource'] = MissingMockCollection('/path/', get_parent=Mock(return_value=parent))
        self.assertEqual(v._allowed_methods(), None)

    def test_options_root(self):
        path = '/'
        v = WebDavView(path=path, acl_class=FullAcl)
        v.__dict__['resource'] = MockObject(path)
        resp = v.options(None, path)
        self.assertEqual(sorted(resp.items()), [
            ('Content-Length', '0'),
            ('Content-Type', 'text/html'),
            ('DAV', '1,2'),
        ])

    def test_options_obj(self):
        path = '/obj'
        v = WebDavView(path=path, _allowed_methods=Mock(return_value=['ALL']), acl_class=FullAcl)
        v.__dict__['resource'] = MockObject(path)
        resp = v.options(None, path)
        self.assertEqual(sorted(resp.items()), [
            ('Allow', 'ALL'),
            ('Allow-Ranges', 'bytes'),
            ('Content-Length', '0'),
            ('Content-Type', 'text/html'),
            ('DAV', '1,2'),
        ])

    def test_options_collection(self):
        path = '/collection/'
        v = WebDavView(path=path, _allowed_methods=Mock(return_value=['ALL']), acl_class=FullAcl)
        v.__dict__['resource'] = MockCollection(path)
        resp = v.options(None, path)
        self.assertEqual(sorted(resp.items()), [
            ('Allow', 'ALL'),
            ('Content-Length', '0'),
            ('Content-Type', 'text/html'),
            ('DAV', '1,2'),
        ])

    def test_get_obj(self):
        path = '/obj.txt'
        v = WebDavView(path=path, _allowed_methods=Mock(return_value=['ALL']), acl_class=FullAcl)
        v.__dict__['resource'] = MockObject(path, read=Mock(return_value="C" * 42))
        resp = v.get(None, path, acl_class=FullAcl)
        self.assertEqual(resp['Etag'], "0" * 40)
        self.assertEqual(resp['Content-Type'], "text/plain")
        self.assertEqual(resp['Last-Modified'], "Wed, 24 Dec 2014 06:00:00 GMT")
        self.assertEqual(resp.content, "C" * 42)

    @patch('djangodav.views.render_to_response', Mock(return_value=HttpResponse('listing')))
    def test_head_object(self):
        path = '/object.txt'
        v = WebDavView(path=path, base_url='/base', _allowed_methods=Mock(return_value=['ALL']), acl_class=FullAcl)
        v.__dict__['resource'] = MockObject(path)
        resp = v.head(None, path)
        self.assertEqual("text/plain", resp['Content-Type'])
        self.assertEqual("Wed, 24 Dec 2014 06:00:00 GMT", resp['Last-Modified'])
        self.assertEqual("", resp.content)
        self.assertEqual("0", resp['Content-Length'])

    @patch('djangodav.views.render_to_response', Mock(return_value=HttpResponse('listing')))
    def test_get_collection(self):
        path = '/collection/'
        v = WebDavView(path=path, acl_class=FullAcl, base_url='/base', _allowed_methods=Mock(return_value=['ALL']))
        v.__dict__['resource'] = MockCollection(path)
        resp = v.get(None, path)
        self.assertEqual("listing", resp.content)
        self.assertEqual("Wed, 24 Dec 2014 06:00:00 GMT", resp['Last-Modified'])

    def test_head_collection(self):
        path = '/collection/'
        v = WebDavView(path=path, acl_class=FullAcl, base_url='/base', _allowed_methods=Mock(return_value=['ALL']))
        v.__dict__['resource'] = MockCollection(path)
        resp = v.head(None, path)
        self.assertEqual("", resp.content)
        self.assertEqual("Wed, 24 Dec 2014 06:00:00 GMT", resp['Last-Modified'])
        self.assertEqual("0", resp['Content-Length'])

    def test_put_new(self):
        path = '/object.txt'
        v = WebDavView(path=path, acl_class=FullAcl, resource_class=Mock())
        v.__dict__['resource'] = self.missing_sub_object
        self.missing_sub_object.write = Mock()
        request = HttpRequest()
        resp = v.put(request, path)
        self.missing_sub_object.write.assert_called_with(request)
        self.assertEqual(201, resp.status_code)

    def test_put_exists(self):
        path = '/object.txt'
        v = WebDavView(path=path, acl_class=FullAcl, resource_class=Mock())
        v.__dict__['resource'] = self.sub_object
        self.sub_object.write = Mock()
        request = HttpRequest()
        resp = v.put(request, path)
        self.sub_object.write.assert_called_with(request)
        self.assertEqual(204, resp.status_code)

    def test_put_collection(self):
        path = '/object.txt'
        v = WebDavView(path=path, acl_class=FullAcl, resource_class=Mock())
        v.__dict__['resource'] = self.sub_collection
        self.sub_collection.write = Mock()
        request = HttpRequest()
        resp = v.put(request, path)
        self.assertFalse(self.sub_collection.write.called)
        self.assertEqual(403, resp.status_code)
