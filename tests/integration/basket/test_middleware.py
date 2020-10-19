from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory

from oscar.apps.basket import middleware
from oscar.test.factories.customer import UserFactory


class BasketMiddlewareMixin:

    @staticmethod
    def get_response_for_test(request):
        return HttpResponse()


class TestBasketMiddleware(BasketMiddlewareMixin, TestCase):

    def setUp(self):
        self.middleware = middleware.BasketMiddleware(self.get_response_for_test)
        self.request = RequestFactory().get('/catalogue/')
        self.request.user = AnonymousUser()
        self.middleware(self.request)

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


class TestBasketMiddlewareWithNoBasket(BasketMiddlewareMixin, TestCase):

    def test_basket_is_disabled_for_dashboard_and_admin(self):
        for url in ['/dashboard/catalogue/', '/admin/']:
            basket_middleware = middleware.BasketMiddleware(self.get_response_for_test)
            request = RequestFactory().get(url)
            request.user = UserFactory(is_superuser=True)
            basket_middleware(request)

            self.assertFalse(hasattr(request, 'basket'))
            self.assertFalse(hasattr(request, 'strategy'))
