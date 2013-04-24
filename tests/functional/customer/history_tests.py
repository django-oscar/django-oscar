from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from oscar_testsupport.factories import create_product
from oscar.apps.customer.history_helpers import get_recently_viewed_product_ids
from oscar.templatetags.history_tags import get_back_button
from django.http import HttpRequest


class HistoryHelpersTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.product = create_product()

    def test_viewing_product_creates_cookie(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertTrue('oscar_recently_viewed_products' in response.cookies)

    def test_id_gets_added_to_cookie(self):
        response = self.client.get(self.product.get_absolute_url())
        request = HttpRequest()
        request.COOKIES['oscar_recently_viewed_products'] = response.cookies['oscar_recently_viewed_products'].value
        self.assertTrue(self.product.id in get_recently_viewed_product_ids(request))

    def test_get_back_button(self):
        request = HttpRequest()

        request.META['SERVER_NAME'] = 'test'
        request.META['SERVER_PORT'] = 8000
        request.META['HTTP_REFERER'] = 'http://www.google.com'
        backbutton = get_back_button({'request': request})
        self.assertEqual(backbutton, None)

        request.META['HTTP_REFERER'] = 'http://test:8000/search/'
        backbutton = get_back_button({'request': request})
        self.assertTrue(backbutton)
        self.assertEqual(backbutton['title'], 'Back to search results')


class TestAUserWhoLogsOut(TestCase):
    username = 'customer'
    password = 'cheeseshop'
    email = 'customer@example.com'

    def setUp(self):
        self.client = Client()
        self.product = create_product()
        User.objects.create_user(username=self.username,
                                 email=self.email, password=self.password)
        self.client.login(username=self.username, password=self.password)

    def test_has_their_cookies_deleted_on_logout(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertTrue('oscar_recently_viewed_products' in response.cookies)

        response = self.client.get(reverse('customer:logout'))
        self.assertTrue(('oscar_recently_viewed_products' not in response.cookies)
                        or not
                        self.client.cookies['oscar_recently_viewed_products'].coded_value)
