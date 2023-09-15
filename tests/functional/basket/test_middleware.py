from decimal import Decimal as D
from django.urls import reverse
from oscar.core.compat import get_user_model
from oscar.test.factories import create_product
from oscar.test.testcases import WebTestCase

User = get_user_model()


class TestBasketMiddlewareMessage(WebTestCase):
    csrf_checks = False
    is_anonymous = True

    def test_merged_basket_message(self):
        product = create_product(price=D("10.00"), num_in_stock=10)
        url = reverse("basket:add", kwargs={"pk": product.pk})
        post_params = {"product_id": product.id, "action": "add", "quantity": 1}
        response = self.app.post(url, params=post_params)
        self.assertTrue("oscar_open_basket" in response.test_app.cookies)
        self.user = User.objects.create(
            first_name="lucy", email="lucy@example.com", password="password"
        )
        response = self.app.get(reverse("basket:summary"))
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        message = (
            "We have merged 1 items from a previous session to "
            "your basket. Its content has changed."
        )
        self.assertEqual(messages[0].message, message)
