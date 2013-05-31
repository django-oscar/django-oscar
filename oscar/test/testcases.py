import httplib

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_webtest import WebTest
from purl import URL


class ClientTestCase(TestCase):
    """
    Helper TestCase for using Django's test client.  The class provides
    auto-creation of a user to avoid boilerplate code.
    """
    username = 'dummyuser'
    email = 'dummyuser@example.com'
    password = 'staffpassword'
    is_anonymous = False
    is_staff = False
    is_superuser = False

    def setUp(self):
        self.client = Client()
        if not self.is_anonymous:
            self.login()

    def login(self):
        self.user = self.create_user()
        self.client.login(username=self.username,
                          password=self.password)

    def create_user(self):
        user = User.objects.create_user(self.username,
                                        self.email,
                                        self.password)
        user.is_staff = self.is_staff
        user.is_superuser = self.is_superuser
        user.save()
        return user

    def assertIsRedirect(self, response, expected_url=None):
        self.assertTrue(response.status_code in (httplib.FOUND,
                                                 httplib.MOVED_PERMANENTLY))
        if expected_url:
            location = URL.from_string(response['Location'])
            self.assertEqual(expected_url, location.path())

    def assertRedirectUrlName(self, response, name, kwargs=None):
        self.assertIsRedirect(response)
        location = response['Location'].replace('http://testserver', '')
        self.assertEqual(location, reverse(name, kwargs=kwargs))

    def assertIsOk(self, response):
        self.assertEqual(httplib.OK, response.status_code)

    def assertInContext(self, response, key):
        self.assertTrue(key in response.context,
                        "Context should contain a variable '%s'" % key)


class WebTestCase(WebTest):
    is_staff = False
    is_anonymous = True
    username = 'testuser'
    email = 'testuser@buymore.com'
    password = 'somefancypassword'

    def setUp(self):
        self.user = None
        if not self.is_anonymous or self.is_staff:
            self.user = User.objects.create_user(self.username, self.email,
                                                 self.password)
            self.user.is_staff = self.is_staff
            self.user.save()

    def get(self, url, **kwargs):
        kwargs.setdefault('user', self.user)
        return self.app.get(url, **kwargs)

    def post(self, url, **kwargs):
        kwargs.setdefault('user', self.user)
        return self.app.post(url, **kwargs)

    def assertRedirectsTo(self, response, url_name):
        self.assertTrue(str(response.status_code).startswith('3'))
        location = response.headers['Location']
        redirect_path = location.replace('http://localhost:80', '')
        self.assertEqual(reverse(url_name), redirect_path)
