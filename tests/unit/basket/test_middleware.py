from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import AnonymousUser

from oscar.apps.basket import middleware


class TestBasketMiddleware(TestCase):

    def setUp(self):
        self.middleware = middleware.BasketMiddleware()
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.middleware.process_request(self.request)

    def test_basket_is_attached_to_request(self):
        self.assertTrue(hasattr(self.request, 'basket'))

    def test_strategy_is_attached_to_basket(self):
        self.assertTrue(hasattr(self.request.basket, 'strategy'))

    def test_strategy_is_attached_to_request(self):
        self.assertTrue(hasattr(self.request, 'strategy'))

    def test_get_cookie_basket_handles_invalid_signatures(self):
        request_factory = RequestFactory()
        request_factory.cookies['oscar_open_basket'] = '1:NOTAVALIDHASH'
        request = request_factory.get('/')
        request.cookies_to_delete = []

        cookie_basket = self.middleware.get_cookie_basket("oscar_open_basket", request, None)

        self.assertEqual(None, cookie_basket)
        self.assertIn("oscar_open_basket", request.cookies_to_delete)
