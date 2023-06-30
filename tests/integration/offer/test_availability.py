import datetime
from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer import models
from oscar.core.compat import get_user_model
from oscar.test.factories import OrderDiscountFactory, UserFactory, create_order

User = get_user_model()


class TestAPerUserConditionalOffer(TestCase):
    def setUp(self):
        self.offer = models.ConditionalOffer(max_user_applications=1)
        self.user = UserFactory()

    def test_is_available_with_no_applications(self):
        self.assertTrue(self.offer.is_available())

    def test_max_applications_is_correct_when_no_applications(self):
        self.assertEqual(1, self.offer.get_max_applications(self.user))

    def test_max_applications_is_correct_when_equal_applications(self):
        order = create_order(user=self.user)
        OrderDiscountFactory(order=order, offer_id=self.offer.id, frequency=1)
        self.assertEqual(0, self.offer.get_max_applications(self.user))

    def test_max_applications_is_correct_when_more_applications(self):
        order = create_order(user=self.user)
        OrderDiscountFactory(order=order, offer_id=self.offer.id, frequency=5)
        self.assertEqual(0, self.offer.get_max_applications(self.user))


class TestADateBasedConditionalOffer(TestCase):
    def setUp(self):
        self.start = datetime.date(2011, 1, 1)
        self.end = datetime.date(2011, 2, 1)
        self.offer = models.ConditionalOffer(
            start_datetime=self.start, end_datetime=self.end
        )

    def test_is_available_during_date_range(self):
        test = datetime.date(2011, 1, 10)
        self.assertTrue(self.offer.is_available(test_date=test))

    def test_is_inactive_before_date_range(self):
        test = datetime.date(2010, 3, 10)
        self.assertFalse(self.offer.is_available(test_date=test))

    def test_is_inactive_after_date_range(self):
        test = datetime.date(2011, 3, 10)
        self.assertFalse(self.offer.is_available(test_date=test))

    def test_is_active_on_end_datetime(self):
        self.assertTrue(self.offer.is_available(test_date=self.end))

    def test_active_on_null_end_datetime(self):
        # null end_datetime means offer should never expire
        offer = models.ConditionalOffer(start_datetime=self.start, end_datetime=None)
        test = datetime.date(2017, 3, 10)
        self.assertTrue(offer.is_available(test_date=test))

    def test_active_on_null_start_datetime(self):
        # null start_datetime means offer is active from the beginning of time
        offer = models.ConditionalOffer(start_datetime=None, end_datetime=self.end)
        test = datetime.date(2000, 3, 10)
        self.assertTrue(offer.is_available(test_date=test))

    def test_active_on_null_start_and_end_datetime(self):
        # null datetimes - offer is always available
        offer = models.ConditionalOffer(start_datetime=None, end_datetime=None)
        test = datetime.date(2017, 3, 10)
        self.assertTrue(offer.is_available(test_date=test))


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

    def test_restricts_number_of_applications_correctly_with_fewer_applications_than_max(
        self,
    ):
        self.offer.num_applications = 3
        self.assertEqual(1, self.offer.get_max_applications())

    def test_restricts_number_of_applications_correctly_with_more_applications_than_max(
        self,
    ):
        self.offer.num_applications = 5
        self.assertEqual(0, self.offer.get_max_applications())


class TestCappedDiscountConditionalOffer(TestCase):
    def setUp(self):
        self.offer = models.ConditionalOffer(
            max_discount=D("100.00"), total_discount=D("0.00")
        )

    def test_is_available_when_below_threshold(self):
        self.assertTrue(self.offer.is_available())

    def test_is_inactive_when_on_threshold(self):
        self.offer.total_discount = self.offer.max_discount
        self.assertFalse(self.offer.is_available())

    def test_is_inactive_when_above_threshold(self):
        self.offer.total_discount = self.offer.max_discount + D("10.00")
        self.assertFalse(self.offer.is_available())


class TestASuspendedOffer(TestCase):
    def setUp(self):
        self.offer = models.ConditionalOffer(status=models.ConditionalOffer.SUSPENDED)

    def test_is_unavailable(self):
        self.assertFalse(self.offer.is_available())

    def test_lists_suspension_as_an_availability_restriction(self):
        restrictions = self.offer.availability_restrictions()
        self.assertEqual(1, len(restrictions))
