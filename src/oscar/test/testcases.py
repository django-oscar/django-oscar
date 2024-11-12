from http import client as http_client

from django.contrib.auth.models import Permission
from django.urls import reverse
from django_webtest import WebTest
from purl import URL

from oscar.core.compat import get_user_model

User = get_user_model()


def add_permissions(user, permissions):
    """
    Grant permissions to the passed user

    :param permissions: e.g. ['partner.dashboard_access']
    """
    for permission in permissions:
        app_label, __, codename = permission.partition(".")
        if codename:
            perm = Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
            user.user_permissions.add(perm)


class WebTestCase(WebTest):
    is_staff = False
    is_anonymous = False
    is_superuser = False

    username = "testuser"
    email = "testuser@buymore.com"
    password = "somefancypassword"
    permissions = []

    def setUp(self):
        self.user = None

        if not self.is_anonymous:
            self.user = self.create_user(self.username, self.email, self.password)
            self.user.is_staff = self.is_staff
            add_permissions(self.user, self.permissions)
            self.user.save()

    def create_user(self, username=None, email=None, password=None):
        """
        Create a user for use in a test.

        As usernames are optional in newer versions of Django, it only sets it
        if exists.
        """
        kwargs = {"email": email, "password": password}
        fields = {f.name: f for f in User._meta.get_fields()}

        if "username" in fields:
            kwargs["username"] = username
        return User.objects.create_user(**kwargs)

    def get(self, url, **kwargs):
        kwargs.setdefault("user", self.user)
        return self.app.get(url, **kwargs)

    def post(self, url, **kwargs):
        kwargs.setdefault("user", self.user)
        return self.app.post(url, **kwargs)

    # Custom assertions

    def assertIsRedirect(self, response, expected_url=None):
        self.assertTrue(
            response.status_code in (http_client.FOUND, http_client.MOVED_PERMANENTLY)
        )
        if expected_url:
            location = URL.from_string(response["Location"])
            self.assertEqual(expected_url, location.path())

    def assertIsNotRedirect(self, response):
        self.assertIsOk(response)
        self.assertTrue(
            response.status_code
            not in (http_client.FOUND, http_client.MOVED_PERMANENTLY)
        )

    def assertRedirectsTo(self, response, url_name, kwargs=None):
        """
        Asserts that a response is a redirect to a given URL name.
        """
        self.assertIsRedirect(response)
        location = response.headers["Location"]
        for unwanted in ["http://localhost:80", "http://testserver"]:
            location = location.replace(unwanted, "")
        self.assertEqual(reverse(url_name, kwargs=kwargs), location)

    def assertNoAccess(self, response, msg=None):
        self.assertContext(response)
        self.assertTrue(
            response.status_code in (http_client.NOT_FOUND, http_client.FORBIDDEN), msg
        )

    def assertIsOk(self, response, msg=None):
        self.assertEqual(http_client.OK, response.status_code, msg)

    def assertContext(self, response):
        self.assertTrue(response.context is not None, "No context was returned")

    def assertInContext(self, response, key):
        self.assertContext(response)
        self.assertTrue(
            key in response.context, "Context should contain a variable '%s'" % key
        )

    def assertNotInContext(self, response, key):
        self.assertContext(response)
        self.assertTrue(
            key not in response.context,
            "Context should not contain a variable '%s'" % key,
        )
