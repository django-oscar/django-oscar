from decimal import Decimal as D
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.core.signing import Signer
from django.http import HttpResponse
from django.test import TestCase
from oscar.apps.basket import middleware
from oscar.apps.customer.auth_backends import EmailBackend
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from oscar.test.basket import add_product
from oscar.test.utils import RequestFactory

Basket = get_model("basket", "Basket")
CatalogueView = get_class("catalogue.views", "CatalogueView")
User = get_user_model()


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
        request_factory = RequestFactory()
        request = request_factory.get("/")
        request.user = AnonymousUser()
        self.middleware(request)
        # add product to anonymous user's basket
        basket = request.basket
        basket.save()
        add_product(basket, D("12.00"), 1)
        basket_hash = Signer().sign(basket.id)
        cookie_key = settings.OSCAR_BASKET_COOKIE_OPEN
        request_factory.cookies[cookie_key] = basket_hash
        # test cookie_basket
        cookie_basket = self.middleware.get_cookie_basket(cookie_key, request, None)
        self.assertEqual(basket, cookie_basket)

        # create User
        username, email, password = "lucy", "lucy@example.com", "password"
        User.objects.create_user(username, email, password)

        # login as registered user
        backend = EmailBackend()
        user = backend.authenticate(None, email, password)
        request = request_factory.get("/")
        request.user = user

        # call CatalogueView and get response
        view = CatalogueView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        messages = get_messages(request)
        message = (
            "We have merged 1 items from a previous session to "
            "your basket. Its content has changed."
        )
        self.assertEqual(messages[0].message, message)
