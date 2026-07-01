from http import client as http_client

from django.urls import reverse

from oscar.test.factories import create_order
from oscar.test.testcases import WebTestCase


class TestAnAnonymousUser(WebTestCase):
    def test_gets_a_302_when_requesting_an_unknown_order(self):
        path = reverse(
            "customer:anon-order", kwargs={"order_number": 1000, "hash": "1231231232"}
        )
        response = self.app.get(path, status="*")

        self.assertEqual(http_client.FOUND, response.status_code)

    def test_can_see_order_status(self):
        email = "henk@oscarcommerce.com"
        order = create_order(guest_email=email)
        sesh = self.client.session
        sesh["anon_order_email"] = email
        sesh.save()
        path = reverse(
            "customer:anon-order",
            kwargs={"order_number": order.number, "hash": order.verification_hash()},
        )
        response = self.client.get(path)
        self.assertEqual(http_client.OK, response.status_code)

    def test_gets_302_when_using_incorrect_hash(self):
        order = create_order()
        path = reverse(
            "customer:anon-order", kwargs={"order_number": order.number, "hash": "bad"}
        )
        response = self.app.get(path, status="*")
        self.assertEqual(http_client.FOUND, response.status_code)

    def test_gets_302_when_using_incorrect_email(self):
        order = create_order(guest_email="henk@oscarcommerce.com")
        sesh = self.client.session
        sesh["anon_order_email"] = "john@oscarcommerce.com"
        sesh.save()
        path = reverse(
            "customer:anon-order",
            kwargs={"order_number": order.number, "hash": order.verification_hash()},
        )
        response = self.client.get(path)
        self.assertEqual(http_client.FOUND, response.status_code)

    def test_anonymous_order_form(self):
        email = "henk@oscarcommerce.com"
        order = create_order(guest_email=email)
        form_url = reverse(
            "customer:anon-order-form",
            kwargs={"order_number": order.number, "hash": order.verification_hash()},
        )
        response = self.client.post(form_url, data={"email": email})
        success_url = reverse(
            "customer:anon-order",
            kwargs={"order_number": order.number, "hash": order.verification_hash()},
        )

        self.assertEqual(http_client.FOUND, response.status_code)
        self.assertEqual(response.url, success_url)
