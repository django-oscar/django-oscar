from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models
from oscar.apps.order.models import OrderDiscount
from oscar.core.compat import get_user_model
from oscar.test.factories import create_order


User = get_user_model()


class TestAPerUserConditionalOffer(TestCase):

    def setUp(self):
        self.offer = models.ConditionalOffer(max_user_applications=1)
        self.user = G(User)

    def test_is_available_with_no_applications(self):
        self.assertTrue(self.offer.is_available())

    def test_max_applications_is_correct_when_no_applications(self):
        self.assertEqual(1, self.offer.get_max_applications(self.user))

    def test_max_applications_is_correct_when_equal_applications(self):
        order = create_order(user=self.user)
        G(OrderDiscount, order=order, offer_id=self.offer.id, frequency=1)
        self.assertEqual(0, self.offer.get_max_applications(self.user))

    def test_max_applications_is_correct_when_more_applications(self):
        order = create_order(user=self.user)
        G(OrderDiscount, order=order, offer_id=self.offer.id, frequency=5)
        self.assertEqual(0, self.offer.get_max_applications(self.user))
