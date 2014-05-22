from os.path import dirname
from base64 import b64encode

from django.test import TestCase
from django.test.client import RequestFactory

from djangodav.views import DavView
from djangodav.fs.resources import DummyReadFSDavResource
from djangodav.auth.rest import RestAuthViewMixIn

from rest_framework.authentication import SessionAuthentication as RestSessionAuthentication, \
                                          BasicAuthentication as RestBasicAuthentication
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
    
    def assertIsAuthorized(self, response):
        self.assertIsInstance(response, HttpResponse)
        self.assertNotIsInstance(response, HttpResponseUnAuthorized)
        
    def assertIsNotAuthorized(self, response):
        self.assertIsInstance(response, HttpResponseUnAuthorized)
      
    def assertHasAuthenticateHeader(self, response):
        self.assertEqual(response['WWW-Authenticate'], 'Basic realm="api"')
      
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
        request = RequestFactory().get('/', **{'HTTP_AUTHORIZATION': 'Basic %s' % b64encode('root:test')})
        response = v(request, '/')
        self.assertIsAuthorized(response)
    
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
        request = RequestFactory().get('/', **{'HTTP_AUTHORIZATION': 'Basic %s' % b64encode('root:test')})
        response = v(request, '/')
        self.assertIsAuthorized(response)
