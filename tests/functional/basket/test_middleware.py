from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse
from oscar.apps.basket import middleware
from oscar.core.compat import get_user_model
from oscar.test.factories import create_product
from oscar.test.utils import RequestFactory

User = get_user_model()


class BasketMiddlewareTest(TestCase):
    @staticmethod
    def get_response_for_test(request):
        return HttpResponse()

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            first_name="lucy", email="lucy@example.com", password="password"
        )
        self.middleware = middleware.BasketMiddleware(self.get_response_for_test)
        self.request = RequestFactory().get("/")
        self.request.user = AnonymousUser()
        self.middleware(self.request)

    def test_merged_basket_message(self):
        product = create_product()
        url = reverse("basket:add", kwargs={"pk": product.pk})
        post_params = {
            "product_id": product.id,
            "action": "add",
            "quantity": 1,
        }
        response = self.client.post(url, post_params)
        self.assertIsRedirect(response)
        
        basket_cookie = response.cookies.get(
            settings.OSCAR_BASKET_COOKIE_OPEN, None)

        self.assertIsNotNone(basket_cookie)

        self.client.force_login(self.user)
        response = self.client.get(reverse("basket:summary"))

        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        message = (
            "We have merged 1 items from a previous session to "
            "your basket. Its content has changed."
        )
        self.assertEqual(messages[0].message, message)
