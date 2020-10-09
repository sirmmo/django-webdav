import sys
from os.path import dirname
from base64 import b64encode

from django.test import TestCase
from django.test.client import RequestFactory
try:
    from django.utils.unittest import skipUnless
except ImportError:
    from unittest import skipUnless

from djangodav.views import DavView
from djangodav.fs.resources import DummyReadFSDavResource
from djangodav.auth.rest import RestAuthViewMixIn

try:
    import rest_framework
    from rest_framework.authentication import SessionAuthentication as RestSessionAuthentication, \
                                          BasicAuthentication as RestBasicAuthentication
except ImportError:
    rest_framework = None

from djangodav.responses import HttpResponseUnAuthorized
from django.contrib.auth import get_user_model
from djangodav.locks import DummyLock
from djangodav.acls import ReadOnlyAcl
from django.http.response import HttpResponse

class TestFSResource(DummyReadFSDavResource):
    """ just a test resource """
    root = dirname(__file__)

class TestDAVView(RestAuthViewMixIn, DavView):
    """ dummy view """
    resource_class= TestFSResource 
    acl_class = ReadOnlyAcl
    lock_class = DummyLock 
            
class RestAuthTest(TestCase):
    """ test authentication through Django Rest Framework. This will
        only work when RestFramework is actually installed.          """
    
    def setUp(self):
        self.user = get_user_model()(username='root', is_active=True)
        self.user.set_password('test')
        self.user.save()
    
    @skipUnless(rest_framework, "required Django Rest Framework")
    def assertIsAuthorized(self, response):
        self.assertIsInstance(response, HttpResponse)
        self.assertNotIsInstance(response, HttpResponseUnAuthorized)
        
    @skipUnless(rest_framework, "required Django Rest Framework")
    def assertIsNotAuthorized(self, response):
        self.assertIsInstance(response, HttpResponseUnAuthorized)
      
    @skipUnless(rest_framework, "required Django Rest Framework")
    def assertHasAuthenticateHeader(self, response):
        self.assertEqual(response['WWW-Authenticate'], 'Basic realm="api"')
      
    @skipUnless(rest_framework, "required Django Rest Framework")
    def test_auth_session(self):
        """ test whether we can authenticate through Django session """        
        
        class RestAuthDavView(TestDAVView):
            authentications = (RestSessionAuthentication(),)
        v = RestAuthDavView.as_view()
            
        # get with no authentication yields HttpResponseUnAuthorized
        request = RequestFactory().get('/')
        response = v(request, '/')
        self.assertIsNotAuthorized(response)
    
        # get with authentication goes through
        request = RequestFactory().get('/')
        # in the regular case, session handling would be done in
        # middleware. RestSessionAuthentication only checks for
        # request.user, so we just fake that
        request.user = self.user
        response = v(request, '/')
        self.assertIsAuthorized(response)
    
    @skipUnless(rest_framework, "required Django Rest Framework")
    def test_auth_basic(self):
        """ test whether we can authenticate through Basic auth """

        class RestAuthDavView(TestDAVView):
            authentications = (RestBasicAuthentication(),)
        v = RestAuthDavView.as_view()
        
        # get with no authentication yields HttpResponseUnAuthorized
        request = RequestFactory().get('/')
        response = v(request, '/')
        self.assertIsNotAuthorized(response)
        self.assertHasAuthenticateHeader(response)

        # get with session authentication does not get through
        request = RequestFactory().get('/')
        request.user = self.user
        response = v(request, '/')
        self.assertIsNotAuthorized(response)

        # get with basic authentication goes through
        if sys.version_info < (3, 0, 0): #py2
            b64encode_str = b64encode('root:test')
        else:
            b64encode_str = b64encode(b'root:test').decode('utf-8')
        request = RequestFactory().get('/', **{'HTTP_AUTHORIZATION': 'Basic %s' % b64encode_str})
        response = v(request, '/')
        self.assertIsAuthorized(response)
    
    @skipUnless(rest_framework, "required Django Rest Framework")
    def test_auth_multiple(self):
        """ test whether we can authenticate through either Session or Basic auth """
        
        class RestAuthDavView(TestDAVView):
            authentications = (RestBasicAuthentication(), RestSessionAuthentication(),)
        v = RestAuthDavView.as_view()
        
        # get with no authentication yields HttpResponseUnAuthorized
        request = RequestFactory().get('/')
        response = v(request, '/')
        self.assertIsNotAuthorized(response)
        self.assertHasAuthenticateHeader(response)
        
        # get with session authentication goes through
        request = RequestFactory().get('/')
        request.user = self.user
        response = v(request, '/')
        self.assertIsAuthorized(response)    
    
        # get with basic authentication goes through
        if sys.version_info < (3, 0, 0): #py2
            b64encode_str = b64encode('root:test')
        else:
            b64encode_str = b64encode(b'root:test').decode('utf-8')
        request = RequestFactory().get('/', **{'HTTP_AUTHORIZATION': 'Basic %s' % b64encode_str})
        response = v(request, '/')
        self.assertIsAuthorized(response)
