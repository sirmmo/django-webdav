import mimetypes, urllib, urlparse, re
from xml.etree import ElementTree

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseNotAllowed, HttpResponseBadRequest, \
    HttpResponseNotModified
from django.utils.http import http_date, parse_etags
from django.shortcuts import render_to_response

from djangodav.acls import DavAcl
from djangodav.response import ResponseException, HttpResponsePreconditionFailed, HttpResponseCreated, HttpResponseNoContent, \
    HttpResponseConflict, HttpResponseMediatypeNotSupported, HttpResponseBadGateway, HttpResponseNotImplemented, \
    HttpResponseMultiStatus
from djangodav.lock import DavLock
from djangodav.property import DavProperty
from djangodav.request import DavRequest
from djangodav.utils import parse_time


PATTERN_IF_DELIMITER = re.compile(r'(<([^>]+)>)|(\(([^\)]+)\))')


class BaseDavServer(object):
    resource_class = None
    lock_class = DavLock
    request_class = DavRequest
    acl_class = DavAcl
    property_class = DavProperty

    def __init__(self, request, path):
        self.request = self.request_class(self, request, path)
        self.props = self.property_class(self)
        self.locks = self.lock_class(self)

    def get_access(self, path):
        """Return permission as DavAcl object. A DavACL should have the following attributes:
        read, write, delete, create, relocate, list. By default we implement a read-only
        system."""
        return self.acl_class(listing=True, read=True, full=False)

    def get_resource(self, path):
        """Return a DavResource object to represent the given path."""
        return self.resource_class(self, path)

    def get_depth(self, default='infinity'):
        depth = str(self.request.META.get('HTTP_DEPTH', default)).lower()
        if not depth in ('0', '1', 'infinity'):
            raise ResponseException(HttpResponseBadRequest('Invalid depth header value %s' % depth))
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
                raise ResponseException(HttpResponsePreconditionFailed())
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
                    raise ResponseException(HttpResponseNotModified())
                raise ResponseException(HttpResponsePreconditionFailed())
            # Ignore If-Modified-Since header...
            cond_if_modified_since = False
        cond_if_unmodified_since = self.request.META.get('HTTP_IF_UNMODIFIED_SINCE', None)
        if cond_if_unmodified_since:
            cond_if_unmodified_since = parse_time(cond_if_unmodified_since)
            if cond_if_unmodified_since and cond_if_unmodified_since <= mtime:
                raise ResponseException(HttpResponsePreconditionFailed())
        if cond_if_modified_since:
            # This previously evaluated True and is not being ignored...
            raise ResponseException(HttpResponseNotModified())
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
                return HttpResponseNotAllowed()
            return handler()
        except ResponseException, e:
            return e.response

    def doGET(self, head=False):
        res = self.get_resource(self.request.path)
        acl = self.get_access(res.path)
        if not res.exists():
            return HttpResponseNotFound()
        if not head and res.isdir():
            if not acl.listing:
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
        acl = self.get_access(res.path)
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
        acl = self.get_access(res.path)
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
        acl = self.get_access(res.path)
        if not acl.create:
            return HttpResponseForbidden()
        res.mkdir()
        return HttpResponseCreated()

    def doCOPY(self, move=False):
        res = self.get_resource(self.request.path)
        if not res.exists():
            return HttpResponseNotFound()
        acl = self.get_access(res.path)
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
        acl = self.get_access(res.path)
        if not acl.listing:
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