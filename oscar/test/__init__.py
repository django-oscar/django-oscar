import httplib
from contextlib import contextmanager

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from purl import URL


@contextmanager
def patch_settings(**kwargs):
    from django.conf import settings
    backup = {}
    for key, value in kwargs.items():
        if hasattr(settings, key):
            backup[key] = getattr(settings, key)
        setattr(settings, key, value)
    yield
    for key, value in backup.items():
        setattr(settings, key, value)


class ClientTestCase(TestCase):
    username = 'dummyuser'
    email = 'dummyuser@example.com'
    password = 'staffpassword'
    is_anonymous = False
    is_staff = False
    is_superuser = False

    def setUp(self):
        self.client = Client()
        if not self.is_anonymous:
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

    def assertRedirectUrlName(self, response, name):
        self.assertIsRedirect(response)
        location = response['Location'].replace('http://testserver', '')
        self.assertEqual(location, reverse(name))

    def assertIsOk(self, response):
        self.assertEqual(httplib.OK, response.status_code)

    def assertInContext(self, response, key):
        self.assertTrue(key in response.context, "Context should contain a variable '%s'" % key)
