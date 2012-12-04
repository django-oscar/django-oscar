from decimal import Decimal as D
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models
from oscar.apps.order.models import OrderDiscount
from oscar_testsupport.factories import create_order


class TestADateBasedConditionalOffer(TestCase):

    def setUp(self):
        self.start = datetime.date(2011, 01, 01)
        self.end = datetime.date(2011, 02, 01)
        self.offer = models.ConditionalOffer(start_date=self.start,
                                             end_date=self.end)

    def test_is_available_during_date_range(self):
        test = datetime.date(2011, 01, 10)
        self.assertTrue(self.offer.is_available(test_date=test))

    def test_is_inactive_before_date_range(self):
        test = datetime.date(2010, 03, 10)
        self.assertFalse(self.offer.is_available(test_date=test))

    def test_is_inactive_after_date_range(self):
        test = datetime.date(2011, 03, 10)
        self.assertFalse(self.offer.is_available(test_date=test))

    def test_is_active_on_end_date(self):
        self.assertTrue(self.offer.is_available(test_date=self.end))


class TestAConsumptionFrequencyBasedConditionalOffer(TestCase):

    def setUp(self):
        self.offer = models.ConditionalOffer(max_global_applications=4)

    def test_is_available_with_no_applications(self):
        self.assertTrue(self.offer.is_available())

    def test_is_available_with_fewer_applications_than_max(self):
        self.offer.num_applications = 3
        self.assertTrue(self.offer.is_available())

    def test_is_inactive_with_equal_applications_to_max(self):
        self.offer.num_applications = 4
        self.assertFalse(self.offer.is_available())

    def test_is_inactive_with_more_applications_than_max(self):
        self.offer.num_applications = 4
        self.assertFalse(self.offer.is_available())

    def test_restricts_number_of_applications_correctly_with_no_applications(self):
        self.assertEqual(4, self.offer.get_max_applications())

    def test_restricts_number_of_applications_correctly_with_fewer_applications_than_max(self):
        self.offer.num_applications = 3
        self.assertEqual(1, self.offer.get_max_applications())

    def test_restricts_number_of_applications_correctly_with_more_applications_than_max(self):
        self.offer.num_applications = 5
        self.assertEqual(0, self.offer.get_max_applications())


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


class TestCappedDiscountConditionalOffer(TestCase):

    def setUp(self):
        self.offer = models.ConditionalOffer(
            max_discount=D('100.00'),
            total_discount=D('0.00'))

    def test_is_available_when_below_threshold(self):
        self.assertTrue(self.offer.is_available())

    def test_is_inactive_when_on_threshold(self):
        self.offer.total_discount = self.offer.max_discount
        self.assertFalse(self.offer.is_available())

    def test_is_inactive_when_above_threshold(self):
        self.offer.total_discount = self.offer.max_discount + D('10.00')
        self.assertFalse(self.offer.is_available())
