from decimal import Decimal as D
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.http import HttpResponse
from oscar.apps.basket import middleware
from oscar.core.compat import get_user_model
from oscar.test.basket import add_product
from oscar.test.testcases import WebTestCase
from oscar.test.utils import RequestFactory

User = get_user_model()


class BasketMiddlewareTest(WebTestCase):
    @staticmethod
    def get_response_for_test(request):
        return HttpResponse()

    def setUp(self):
        self.middleware = middleware.BasketMiddleware(self.get_response_for_test)
        self.request = RequestFactory().get("/")
        self.request.user = AnonymousUser()
        self.middleware(self.request)
        self.user = None

    def test_merged_basket_message(self):
        # add product to anonymous user's basket
        basket = self.middleware.get_basket(self.request)
        add_product(basket, D("5.00"), 1)
        self.assertEqual(basket.owner, None)
        # get hash from basket
        basket_hash = self.middleware.get_basket_hash(basket.id)

        user = self.create_user(self.username, self.email, self.password)
        user.save()

        request_factory = RequestFactory()
        request_factory.cookies[settings.OSCAR_BASKET_COOKIE_OPEN] = basket_hash
        request = request_factory.get("/")
        request.user = user
        request.cookies_to_delete = []

        # call get_basket() to merge baskets
        basket = self.middleware.get_basket(request)
        self.assertEqual(basket.owner, user)
        self.assertEqual(basket.lines.count(), 1)

        messages = get_messages(request)
        self.assertEqual(len(messages), 1)
        message = (
            "We have merged 1 items from a previous session to "
            "your basket. Its content has changed."
        )
        self.assertEqual(messages[0].message, message)
