from decimal import Decimal as D

from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.shipping import models


class TestWeightBasedMethod(TestCase):

    def test_doesnt_allow_negative_default_weights(self):
        method = models.WeightBased(
            name="Dummy", default_weight=D('-0.1'))
        with self.assertRaises(ValidationError):
            method.full_clean()


class TestWeightBand(TestCase):

    def test_doesnt_allow_negative_upper_limit(self):
        band = models.WeightBand(upper_limit=D('-0.1'))
        with self.assertRaises(ValidationError) as cm:
            band.full_clean()
        self.assertTrue('upper_limit' in cm.exception.message_dict)

    def test_doesnt_allow_negative_charge(self):
        band = models.WeightBand(charge=D('-0.1'))
        with self.assertRaises(ValidationError) as cm:
            band.full_clean()
        self.assertTrue('charge' in cm.exception.message_dict)
