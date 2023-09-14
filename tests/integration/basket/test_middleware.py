from decimal import Decimal as D
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.core.signing import Signer
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from oscar.apps.basket import middleware
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class
from oscar.test.basket import add_product

User = get_user_model()
AccountAuthView = get_class("customer.views", "AccountAuthView")

class TestBasketMiddleware(TestCase):
    @staticmethod
    def get_response_for_test(request):
        return HttpResponse()

    def setUp(self):
        self.middleware = middleware.BasketMiddleware(self.get_response_for_test)
        self.request = RequestFactory().get("/")
        self.request.user = AnonymousUser()
        self.middleware(self.request)

    def test_basket_is_attached_to_request(self):
        self.assertTrue(hasattr(self.request, "basket"))

    def test_strategy_is_attached_to_basket(self):
        # pylint: disable=no-member
        self.assertTrue(hasattr(self.request.basket, "strategy"))

    def test_strategy_is_attached_to_request(self):
        self.assertTrue(hasattr(self.request, "strategy"))

    def test_get_cookie_basket_handles_invalid_signatures(self):
        request_factory = RequestFactory()
        request_factory.cookies["oscar_open_basket"] = "1:NOTAVALIDHASH"
        request = request_factory.get("/")
        request.cookies_to_delete = []

        cookie_basket = self.middleware.get_cookie_basket(
            "oscar_open_basket", request, None
        )

        self.assertEqual(None, cookie_basket)
        self.assertIn("oscar_open_basket", request.cookies_to_delete)

    def test_merged_basket_message(self):
        # add product to anonymous user's basket
        basket = self.request.basket
        add_product(basket, D("12.00"), 1)
        basket.save()
        # set cookie_basket
        basket_hash = Signer().sign(basket.id)
        request_factory = RequestFactory()
        request_factory.cookies["oscar_open_basket"] = basket_hash
        request = request_factory.get("/")
        request.user = AnonymousUser()
        request.cookies_to_delete = []
        cookie_basket = self.middleware.get_cookie_basket(
            "oscar_open_basket", request, None
        )
        self.assertEqual(basket, cookie_basket)
        # create User
        username, email, password = "lucy", "lucy@example.com", "password"
        request = request_factory.get("/")
        request.user = User.objects.create_user(username, email, password)
        # login as registered user
        data = {"username": "lucy@example.com", "password": password}
        request = request_factory.post("customer:login", data=data)
        view = AccountAuthView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        messages = get_messages(request)
        message = (
            "We have merged 1 items from a previous session to "
            "your basket. Its content has changed."
        )
        self.assertEqual(messages[0].message, message)
