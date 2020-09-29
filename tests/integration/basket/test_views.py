from django.test import TestCase
from django.urls import reverse

from oscar.apps.basket import views
from oscar.test import factories
from tests.fixtures import RequestFactory


class TestBasketSummaryView(TestCase):
    def setUp(self):
        self.url = reverse('basket:summary')
        self.country = factories.CountryFactory()
        self.user = factories.UserFactory()

    def test_default_shipping_address(self):
        user_address = factories.UserAddressFactory(
            country=self.country, user=self.user, is_default_for_shipping=True
        )
        request = RequestFactory().get(self.url, user=self.user)
        view = views.BasketView(request=request)
        self.assertEqual(view.get_default_shipping_address(), user_address)

    def test_default_shipping_address_for_anonymous_user(self):
        request = RequestFactory().get(self.url)
        view = views.BasketView(request=request)
        self.assertIsNone(view.get_default_shipping_address())
