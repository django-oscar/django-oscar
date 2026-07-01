from http.cookies import _unquote

from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

from oscar.core.compat import get_user_model
from oscar.core.loading import get_class
from oscar.templatetags.history_tags import get_back_button
from oscar.test.factories import create_product
from oscar.test.testcases import WebTestCase

CustomerHistoryManager = get_class("customer.history", "CustomerHistoryManager")
User = get_user_model()
COOKIE_NAME = settings.OSCAR_RECENTLY_VIEWED_COOKIE_NAME


class HistoryHelpersTest(WebTestCase):
    def setUp(self):
        self.product = create_product()

    def test_viewing_product_creates_cookie(self):
        response = self.app.get(self.product.get_absolute_url())
        self.assertTrue(COOKIE_NAME in response.test_app.cookies)

    def test_id_gets_added_to_cookie(self):
        response = self.app.get(self.product.get_absolute_url())
        request = HttpRequest()
        request.COOKIES[COOKIE_NAME] = _unquote(response.test_app.cookies[COOKIE_NAME])
        self.assertTrue(self.product.id in CustomerHistoryManager.extract(request))

    def test_get_back_button(self):
        request = HttpRequest()

        request.META["SERVER_NAME"] = "test"
        request.META["SERVER_PORT"] = 8000
        request.META["HTTP_REFERER"] = "http://www.google.com"
        backbutton = get_back_button({"request": request})
        self.assertEqual(backbutton, None)

        request.META["HTTP_REFERER"] = "http://test:8000/search/"
        backbutton = get_back_button({"request": request})
        self.assertTrue(backbutton)
        self.assertEqual(backbutton["title"], "Back to search results")


class TestAUserWhoLogsOut(WebTestCase):
    username = "customer"
    password = "cheeseshop"
    email = "customer@example.com"

    def setUp(self):
        self.product = create_product()
        self.user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password
        )

    def test_has_their_cookies_deleted_on_logout(self):
        response = self.get(self.product.get_absolute_url())
        self.assertTrue(COOKIE_NAME in response.test_app.cookies)

        response = self.get(reverse("customer:logout"))
        self.assertTrue(
            (COOKIE_NAME not in response.test_app.cookies)
            or not self.app.cookies.get("oscar_recently_viewed_products", None)
        )
