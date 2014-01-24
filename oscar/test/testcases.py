from six.moves import http_client

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission
from django_webtest import WebTest
from purl import URL

from oscar.core.compat import get_user_model


User = get_user_model()


def add_permissions(user, permissions):
    """
    :param permissions: e.g. ['partner.dashboard_access']
    """
    for permission in permissions:
        app_label, _, codename = permission.partition('.')
        perm = Permission.objects.get(content_type__app_label=app_label,
                                      codename=codename)
        user.user_permissions.add(perm)


class WebTestCase(WebTest):
    is_staff = False
    is_anonymous = False
    username = 'testuser'
    email = 'testuser@buymore.com'
    password = 'somefancypassword'
    is_superuser = False
    permissions = []

    def setUp(self):
        self.user = None
        if not self.is_anonymous or self.is_staff:
            self.user = User.objects.create_user(self.username, self.email,
                                                 self.password)
            self.user.is_staff = self.is_staff
            perms = self.permissions
            add_permissions(self.user, perms)
            self.user.save()
            self.login()

    def get(self, url, **kwargs):
        kwargs.setdefault('user', self.user)
        return self.app.get(url, **kwargs)

    def post(self, url, **kwargs):
        kwargs.setdefault('user', self.user)
        return self.app.post(url, **kwargs)

    def login(self, username=None, password=None):
        username = username or self.username
        password = password or self.password
        self.client.login(username=username, password=password)

    # Custom assertions

    def assertIsRedirect(self, response, expected_url=None):
        self.assertTrue(response.status_code in (
            http_client.FOUND, http_client.MOVED_PERMANENTLY))
        if expected_url:
            location = URL.from_string(response['Location'])
            self.assertEqual(expected_url, location.path())

    def assertRedirectsTo(self, response, url_name):
        self.assertTrue(str(response.status_code).startswith('3'))
        location = response.headers['Location']
        redirect_path = location.replace('http://localhost:80', '')
        self.assertEqual(reverse(url_name), redirect_path)

    def assertNoAccess(self, response):
        self.assertContext(response)
        self.assertTrue(response.status_code in (http_client.NOT_FOUND,
                                                 http_client.FORBIDDEN))

    def assertRedirectUrlName(self, response, name, kwargs=None):
        self.assertIsRedirect(response)
        location = response['Location'].replace('http://testserver', '')
        self.assertEqual(location, reverse(name, kwargs=kwargs))

    def assertIsOk(self, response):
        self.assertEqual(http_client.OK, response.status_code)

    def assertContext(self, response):
        self.assertTrue(response.context is not None,
                        'No context was returned')

    def assertInContext(self, response, key):
        self.assertContext(response)
        self.assertTrue(key in response.context,
                        "Context should contain a variable '%s'" % key)
