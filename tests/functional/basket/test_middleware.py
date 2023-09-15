from decimal import Decimal as D
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from oscar.apps.basket import middleware, views
from oscar.core.compat import get_user_model
from oscar.test import factories
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
        self.user = factories.UserFactory()

    def test_merged_basket_message(self):
        # add product to anonymous user's basket
        basket = self.middleware.get_basket(self.request)
        add_product(basket, D("5.00"), 1)
        cookie_basket = self.middleware.get_cookie_basket(
            settings.OSCAR_BASKET_COOKIE_OPEN, self.request, None
        )
        self.assertEqual(basket, cookie_basket)
        self.assertEqual(cookie_basket.lines.count(), 1)
        # get hash from cookie_basket and set cookie in new request
        basket_hash = self.middleware.get_basket_hash(basket.id)

        request = RequestFactory().get(self.url, user=self.user)
        request.COOKIES[settings.OSCAR_BASKET_COOKIE_OPEN] = basket_hash
        # call BasketView and check messages from response.context
        view = views.BasketView.as_view()
        response = view(request)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        message = (
            "We have merged 1 items from a previous session to "
            "your basket. Its content has changed."
        )
        self.assertEqual(messages[0].message, message)
