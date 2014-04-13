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

import mimetypes, urllib, urlparse, re
from xml.etree import ElementTree
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseNotAllowed, \
    HttpResponseBadRequest
from django.utils import synch
from django.utils.http import http_date, parse_etags
from django.utils.encoding import smart_unicode
from django.shortcuts import render_to_response
from djangodav.http import HttpPreconditionFailed, HttpNotModified, HttpNotAllowed, HttpError, HttpResponseCreated, \
    HttpResponseNoContent, HttpResponseConflict, HttpResponseMediatypeNotSupported, HttpResponseBadGateway, \
    HttpResponsePreconditionFailed, HttpResponseMultiStatus, HttpResponseNotImplemented
from djangodav.utils import ns_split, rfc3339_date, parse_time


PATTERN_IF_DELIMITER = re.compile(r'(<([^>]+)>)|(\(([^\)]+)\))')


class DavAcl(object):
    """Represents all the permissions that a user might have on a resource. This
    makes it easy to implement virtual permissions."""
    def __init__(self, read=True, write=True, delete=True, create=True, relocate=True, _list=True, _all=None):
        if not all is None:
            self.read = self.write = self.delete = \
                self.create = self.relocate = self.list = _all
        self.read = read
        self.write = write
        self.delete = delete
        self.create = create
        self.relocate = relocate
        self.list = _list


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


class DavLock(object):
    def __init__(self, server):
        self.server = server
        self.lock = synch.RWLock()

    def get(self, res):
        """Gets all active locks for the requested resource. Returns a list of locks."""
        self.lock.reader_enters()
        try:
            pass
        finally:
            self.lock.reader_leaves()

    def acquire(self, res, type, scope, depth, owner, timeout):
        """Creates a new lock for the given resource."""
        self.lock.writer_enters()
        try:
            pass
        finally:
            self.lock.writer_leaves()

    def release(self, lock):
        """Releases the lock referenced by the given lock id."""
        self.lock.writer_enters()
        try:
            pass
        finally:
            self.lock.writer_leaves()

    def del_locks(self, res):
        """Releases all locks for the given resource."""
        self.lock.writer_enters()
        try:
            pass
        finally:
            self.lock.writer_leaves()


class DavServer(object):
    def __init__(self, request, path, property_class=DavProperty, resource_class=DavResource, lock_class=DavLock,
                 acl_class=DavAcl):
        self.request = DavRequest(self, request, path)
        self.resource_class = resource_class
        self.acl_class = acl_class
        self.props = property_class(self)
        self.locks = lock_class(self)

    def get_root(self):
        """Return the root of the file system we wish to export. By default the root
        is read from the DAV_ROOT setting in django's settings.py. You can override
        this method to export a different directory (maybe even different per user)."""
        return getattr(settings, 'DAV_ROOT', None)

    def get_access(self, path):
        """Return permission as DavAcl object. A DavACL should have the following attributes:
        read, write, delete, create, relocate, list. By default we implement a read-only
        system."""
        return self.acl_class(list=True, read=True, all=False)

    def get_resource(self, path):
        """Return a DavResource object to represent the given path."""
        return self.resource_class(self, path)

    def get_depth(self, default='infinity'):
        depth = str(self.request.META.get('HTTP_DEPTH', default)).lower()
        if not depth in ('0', '1', 'infinity'):
            raise HttpResponseBadRequest('Invalid depth header value %s' % depth)
        if depth == 'infinity':
            depth = -1
        else:
            depth = int(depth)
        return depth

    def evaluate_conditions(self, res):
        if not res.exists():
            return
        etag = res.get_etag()
        mtime = res.get_mtime_stamp()
        cond_if_match = self.request.META.get('HTTP_IF_MATCH', None)
        if cond_if_match:
            etags = parse_etags(cond_if_match)
            if '*' in etags or etag in etags:
                raise HttpPreconditionFailed()
        cond_if_modified_since = self.request.META.get('HTTP_IF_MODIFIED_SINCE', False)
        if cond_if_modified_since:
            # Parse and evaluate, but don't raise anything just yet...
            # This might be ignored based on If-None-Match evaluation.
            cond_if_modified_since = parse_time(cond_if_modified_since)
            if cond_if_modified_since and cond_if_modified_since > mtime:
                cond_if_modified_since = True
            else:
                cond_if_modified_since = False
        cond_if_none_match = self.request.META.get('HTTP_IF_NONE_MATCH', None)
        if cond_if_none_match:
            etags = parse_etags(cond_if_none_match)
            if '*' in etags or etag in etags:
                if self.request.method in ('GET', 'HEAD'):
                    raise HttpNotModified()
                raise HttpPreconditionFailed()
            # Ignore If-Modified-Since header...
            cond_if_modified_since = False
        cond_if_unmodified_since = self.request.META.get('HTTP_IF_UNMODIFIED_SINCE', None)
        if cond_if_unmodified_since:
            cond_if_unmodified_since = parse_time(cond_if_unmodified_since)
            if cond_if_unmodified_since and cond_if_unmodified_since <= mtime:
                raise HttpPreconditionFailed()
        if cond_if_modified_since:
            # This previously evaluated True and is not being ignored...
            raise HttpNotModified()
        # TODO: complete If header handling...
        cond_if = self.request.META.get('HTTP_IF', None)
        if cond_if:
            if not cond_if.startswith('<'):
                cond_if = '<*>' + cond_if
            #for (tmpurl, url, tmpcontent, content) in PATTERN_IF_DELIMITER.findall(cond_if):

    def get_response(self):
        handler = getattr(self, 'do' + self.request.method, None)
        try:
            if not callable(handler):
                raise HttpNotAllowed()
            return handler()
        except HttpError, e:
            return e.get_response()

    def doGET(self, head=False):
        res = self.get_resource(self.request.path)
        acl = self.get_access(res.get_abs_path())
        if not res.exists():
            return HttpResponseNotFound()
        if not head and res.isdir():
            if not acl.list:
                return HttpResponseForbidden()
            return render_to_response('djangodav/index.html', {'res': res})
        else:
            if not acl.read:
                return HttpResponseForbidden()
            if head and res.exists():
                response = HttpResponse()
            elif head:
                response = HttpResponseNotFound()
            else:
                use_sendfile = getattr(settings, 'DAV_USE_SENDFILE', '').split()
                if len(use_sendfile) > 0 and use_sendfile[0].lower() == 'x-sendfile':
                    full_path = res.get_abs_path().encode('utf-8')
                    if len(use_sendfile) == 2 and use_sendfile[1] == 'escape':
                        full_path = urllib.quote(full_path)
                    response = HttpResponse()
                    response['X-SendFile'] = full_path
                elif len(use_sendfile) == 2 and use_sendfile[0].lower() == 'x-accel-redir':
                    full_path = res.get_abs_path().encode('utf-8')
                    full_path = url_join(use_sendfile[1], full_path)
                    response = HttpResponse()
                    response['X-Accel-Redirect'] = full_path
                    response['X-Accel-Charset'] = 'utf-8'
                else:
                    # Do things the slow way:
                    response = HttpResponse(res.read())
            if res.exists():
                response['Content-Type'] = mimetypes.guess_type(res.get_name())
                response['Content-Length'] = res.get_size()
                response['Last-Modified'] = http_date(res.get_mtime_stamp())
                response['ETag'] = res.get_etag()
            response['Date'] = http_date()
        return response

    def doHEAD(self):
        return self.doGET(head=True)

    def doPOST(self):
        return HttpResponseNotAllowed('POST method not allowed')

    def doPUT(self):
        res = self.get_resource(self.request.path)
        if res.isdir():
            return HttpResponseNotAllowed()
        if not res.get_parent().exists():
            return HttpResponseNotFound()
        acl = self.get_access(res.get_abs_path())
        if not acl.write:
            return HttpResponseForbidden()
        created = not res.exists()
        res.write(self.request)
        if created:
            return HttpResponseCreated()
        else:
            return HttpResponseNoContent()

    def doDELETE(self):
        res = self.get_resource(self.request.path)
        if not res.exists():
            return HttpResponseNotFound()
        acl = self.get_access(res.get_abs_path())
        if not acl.delete:
            return HttpResponseForbidden()
        self.locks.del_locks(res)
        self.props.del_props(res)
        res.delete()
        response = HttpResponseNoContent()
        response['Date'] = http_date()
        return response

    def doMKCOL(self):
        res = self.get_resource(self.request.path)
        if res.exists():
            return HttpResponseNotAllowed()
        if not res.get_parent().exists():
            return HttpResponseConflict()
        length = self.request.META.get('CONTENT_LENGTH', 0)
        if length and int(length) != 0:
            return HttpResponseMediatypeNotSupported()
        acl = self.get_access(res.get_abs_path())
        if not acl.create:
            return HttpResponseForbidden()
        res.mkdir()
        return HttpResponseCreated()

    def doCOPY(self, move=False):
        res = self.get_resource(self.request.path)
        if not res.exists():
            return HttpResponseNotFound()
        acl = self.get_access(res.get_abs_path())
        if not acl.relocate:
            return HttpResponseForbidden()
        dst = urllib.unquote(self.request.META.get('HTTP_DESTINATION', ''))
        if not dst:
            return HttpResponseBadRequest('Destination header missing.')
        dparts = urlparse.urlparse(dst)
        # TODO: ensure host and scheme portion matches ours...
        sparts = urlparse.urlparse(self.request.build_absolute_uri())
        if sparts.scheme != dparts.scheme or sparts.netloc != dparts.netloc:
            return HttpResponseBadGateway('Source and destination must have the same scheme and host.')
        # adjust path for our base url:
        dst = self.get_resource(dparts.path[len(self.request.get_base()):])
        if not dst.get_parent().exists():
            return HttpResponseConflict()
        overwrite = self.request.META.get('HTTP_OVERWRITE', 'T')
        if overwrite not in ('T', 'F'):
            return HttpResponseBadRequest('Overwrite header must be T or F.')
        overwrite = (overwrite == 'T')
        if not overwrite and dst.exists():
            return HttpResponsePreconditionFailed('Destination exists and overwrite False.')
        depth = self.get_depth()
        if move and depth != -1:
            return HttpResponseBadRequest()
        if depth not in (0, -1):
            return HttpResponseBadRequest()
        dst_exists = dst.exists()
        if move:
            if dst_exists:
                self.locks.del_locks(dst)
                self.props.del_props(dst)
                dst.delete()
            errors = res.move(dst)
        else:
            errors = res.copy(dst, depth=depth)
        self.props.copy_props(res, dst, move=move)
        if move:
            self.locks.del_locks(res)
        if errors:
            response = HttpResponseMultiStatus()
        elif dst_exists:
            response = HttpResponseNoContent()
        else:
            response = HttpResponseCreated()
        return response

    def doMOVE(self):
        return self.doCOPY(move=True)

    def doLOCK(self):
        return HttpResponseNotImplemented()

    def doUNLOCK(self):
        return HttpResponseNotImplemented()

    def doOPTIONS(self):
        response = HttpResponse(mimetype='text/html')
        response['DAV'] = '1,2'
        response['Date'] = http_date()
        if self.request.path in ('/', '*'):
            return response
        res = self.get_resource(self.request.path)
        if not res.exists():
            res = res.get_parent()
            if not res.isdir():
                return HttpResponseNotFound()
            response['Allow'] = 'OPTIONS PUT MKCOL'
        elif res.isdir():
            response['Allow'] = 'OPTIONS HEAD GET DELETE PROPFIND PROPPATCH COPY MOVE LOCK UNLOCK'
        else:
            response['Allow'] = 'OPTIONS HEAD GET PUT DELETE PROPFIND PROPPATCH COPY MOVE LOCK UNLOCK'
            response['Allow-Ranges'] = 'bytes'
        return response

    def doPROPFIND(self):
        res = self.get_resource(self.request.path)
        if not res.exists():
            return HttpResponseNotFound()
        acl = self.get_access(res.get_abs_path())
        if not acl.list:
            return HttpResponseForbidden()
        depth = self.get_depth()
        names_only, props = False, []
        length = self.request.META.get('CONTENT_LENGTH', 0)
        if not length or int(length) != 0:
            #Otherwise, empty prop list is treated as request for ALL props.
            for ev, el in ElementTree.iterparse(self.request):
                if el.tag == '{DAV:}allprop':
                    if props:
                        return HttpResponseBadRequest()
                elif el.tag == '{DAV:}propname':
                    names_only = True
                elif el.tag == '{DAV:}prop':
                    if names_only:
                        return HttpResponseBadRequest()
                    for pr in el:
                        props.append(pr.tag)
        msr = ElementTree.Element('{DAV:}multistatus')
        for child in res.get_descendants(depth=depth, include_self=True):
            response = ElementTree.SubElement(msr, '{DAV:}response')
            ElementTree.SubElement(response, '{DAV:}href').text = child.get_url()
            self.props.get_propstat(child, response, *props)
        response = HttpResponseMultiStatus(ElementTree.tostring(msr, 'UTF-8'), mimetype='application/xml')
        response['Date'] = http_date()
        return response

    def doPROPPATCH(self):
        res = self.get_resource(self.request.path)
        if not res.exists():
            return HttpResponseNotFound()
        depth = self.get_depth(default="0")
        if depth != 0:
            return HttpResponseBadRequest('Invalid depth header value %s' % depth)
