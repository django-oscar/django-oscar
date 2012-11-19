import datetime

from django.test import TestCase

from oscar.apps.offer import models


class TestADateBasedConditionalOffer(TestCase):

    def setUp(self):
        self.start = datetime.date(2011, 01, 01)
        self.end = datetime.date(2011, 02, 01)
        self.offer = models.ConditionalOffer(start_date=self.start,
                                             end_date=self.end)

    def test_is_active_during_date_range(self):
        test = datetime.date(2011, 01, 10)
        self.assertTrue(self.offer.is_active(test))

    def test_is_inactive_before_date_range(self):
        test = datetime.date(2010, 03, 10)
        self.assertFalse(self.offer.is_active(test))

    def test_is_inactive_after_date_range(self):
        test = datetime.date(2011, 03, 10)
        self.assertFalse(self.offer.is_active(test))

    def test_is_inactive_on_end_date(self):
        self.assertFalse(self.offer.is_active(self.end))


class TestAConsumptionFrequencyBasedConditionalOffer(TestCase):

    def setUp(self):
        self.offer = models.ConditionalOffer(max_global_applications=4)

    def test_is_active_with_no_applications(self):
        self.assertTrue(self.offer.is_active())

    def test_is_active_with_fewer_applications_than_max(self):
        self.offer.num_applications = 3
        self.assertTrue(self.offer.is_active())

    def test_is_inactive_with_equal_applications_to_max(self):
        self.offer.num_applications = 4
        self.assertFalse(self.offer.is_active())

    def test_is_inactive_with_more_applications_than_max(self):
        self.offer.num_applications = 4
        self.assertFalse(self.offer.is_active())

    def test_restricts_number_of_applications_correctly_with_no_applications(self):
        self.assertEqual(4, self.offer.get_max_applications())

    def test_restricts_number_of_applications_correctly_with_fewer_applications_than_max(self):
        self.offer.num_applications = 3
        self.assertEqual(1, self.offer.get_max_applications())

    def test_restricts_number_of_applications_correctly_with_more_applications_than_max(self):
        self.offer.num_applications = 5
        self.assertEqual(0, self.offer.get_max_applications())
