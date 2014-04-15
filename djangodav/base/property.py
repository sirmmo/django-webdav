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

from xml.etree import ElementTree

from django.utils import synch
from django.utils.encoding import smart_unicode
from django.utils.http import http_date

from djangodav.utils import ns_split, rfc3339_date


class DavProperty(object):
    LIVE_PROPERTIES = [
        '{DAV:}getetag', '{DAV:}getcontentlength', '{DAV:}creationdate',
        '{DAV:}getlastmodified', '{DAV:}resourcetype', '{DAV:}displayname'
    ]

    def __init__(self, server):
        self.server = server
        self.lock = synch.RWLock()

    def get_dead_names(self, res):
        return []

    def get_dead_value(self, res, name):
        """Implements "dead" property retrival. Thread synchronization is handled outside this method."""
        return

    def set_dead_value(self, res, name, value):
        """Implements "dead" property storage. Thread synchronization is handled outside this method."""
        return

    def del_dead_prop(self, res, name):
        """Implements "dead" property removal. Thread synchronizatioin is handled outside this method."""
        return

    def get_prop_names(self, res, *names):
        return self.LIVE_PROPERTIES + self.get_dead_names(res)

    def get_prop_value(self, res, name):
        self.lock.reader_enters()
        try:
            ns, bare_name = ns_split(name)
            if ns != 'DAV':
                return self.get_dead_value(res, name)
            else:
                value = None
                if bare_name == 'getetag':
                    value = res.get_etag()
                elif bare_name == 'getcontentlength':
                    value = str(res.get_size())
                elif bare_name == 'creationdate':
                    value = rfc3339_date(res.get_ctime_stamp())     # RFC3339:
                elif bare_name == 'getlastmodified':
                    value = http_date(res.get_mtime_stamp())        # RFC1123:
                elif bare_name == 'resourcetype':
                    if res.isdir():
                        value = []
                    else:
                        value = ''
                elif bare_name == 'displayname':
                    value = res.get_name()
                elif bare_name == 'href':
                    value = res.get_url()
            return value
        finally:
            self.lock.reader_leaves()

    def set_prop_value(self, res, name, value):
        self.lock.writer_enters()
        try:
            ns, bare_name = ns_split(name)
            if ns == 'DAV':
                pass  # TODO: handle set-able "live" properties?
            else:
                self.set_dead_value(res, name, value)
        finally:
            self.lock.writer_leaves()

    def del_props(self, res, *names):
        self.lock.writer_enters()
        try:
            avail_names = self.get_prop_names(res)
            if not names:
                names = avail_names
            for name in names:
                ns, bare_name = ns_split(name)
                if ns == 'DAV':
                    pass  # TODO: handle delete-able "live" properties?
                else:
                    self.del_dead_prop(res, name)
        finally:
            self.lock.writer_leaves()

    def copy_props(self, src, dst, *names, **kwargs):
        move = kwargs.get('move', False)
        self.lock.writer_enters()
        try:
            names = self.get_prop_names(src)
            for name in names:
                ns, bare_name = ns_split(name)
                if ns == 'DAV':
                    continue
                self.set_dead_value(dst, name, self.get_prop_value(src, name))
                if move:
                    self.del_dead_prop(self, name)
        finally:
            self.lock.writer_leaves()

    def get_propstat(self, res, el, *names):
        """Returns the XML representation of a resource's properties. Thread synchronization is handled
        in the get_prop_value() method individually for each property."""
        el404, el200 = None, None
        avail_names = self.get_prop_names(res)
        if not names:
            names = avail_names
        for name in names:
            # propname
            # Tag.multistatus(
            #     Tag.response(
            #         Tag.href(url_join(self.base_url, self.resource.get_path())),
            #         Tag.propstat(
            #             Tag.prop(
            #                 Tag.creationdate(),
            #                 Tag.displayname(),
            #                 Tag.getcontentlength(),
            #                 Tag.getlastmodified(),
            #                 Tag.resourcetype(Tag.collection()),
            #             ),
            #             Tag.status(text='HTTP/1.1 200 OK'),
            #         ),
            #     ),
            # )

            if name in avail_names:
                value = self.get_prop_value(res, name)
                if el200 is None:
                    el200 = ElementTree.SubElement(el, '{DAV:}propstat')
                    ElementTree.SubElement(el200, '{DAV:}status').text = 'HTTP/1.1 200 OK'
                prop = ElementTree.SubElement(el200, '{DAV:}prop')
                prop = ElementTree.SubElement(prop, name)
                if isinstance(value, list):
                    prop.append(ElementTree.Element("{DAV:}collection"))
                elif value:
                    prop.text = smart_unicode(value)
            else:
                if el404 is None:
                    el404 = ElementTree.SubElement(el, '{DAV:}propstat')
                    ElementTree.SubElement(el404, '{DAV:}status').text = 'HTTP/1.1 404 Not Found'
                prop = ElementTree.SubElement(el404, '{DAV:}prop')
                prop = ElementTree.SubElement(prop, name)
