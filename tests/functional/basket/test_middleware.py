from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from oscar.core.compat import get_user_model
from oscar.test.factories import create_product
User = get_user_model()


class BasketMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            first_name="lucy", email="lucy@example.com", password="password"
        )

    def test_merged_basket_message(self):       
        product = create_product()
        url = reverse("basket:add", kwargs={"pk": product.pk})
        post_params = {
            "product_id": product.id,
            "action": "add",
            "quantity": 1,
        }
        response = self.client.post(url, post_params, follow=True)
        cookie_key = response.cookies.get(
            settings.OSCAR_BASKET_COOKIE_OPEN, None)
        self.assertIsNotNone(cookie_key)

        self.client.force_login(self.user)
        response = self.client.get(reverse("basket:summary"))

        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        message = (
            "We have merged 1 items from a previous session to "
            "your basket. Its content has changed."
        )
        self.assertEqual(messages[0].message, message)
