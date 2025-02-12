# pylint: disable=redefined-outer-name
from decimal import ROUND_DOWN, Decimal
from unittest.mock import patch

import pytest
from django.test import TestCase, override_settings

from oscar.apps.offer.models import Benefit
from oscar.test import factories


@pytest.fixture
def product_range():
    return factories.RangeFactory()


@pytest.mark.django_db
class TestBenefitProxyModels(object):
    """

    https://docs.djangoproject.com/en/1.11/topics/db/models/#proxy-models

    """

    def test_name_and_description(self, product_range):
        """
        Tests that the benefit proxy classes all return a name and
        description. Unfortunately, the current implementations means
        a valid range is required.w
        """
        for benefit_type, __ in Benefit.TYPE_CHOICES:
            benefit = Benefit(type=benefit_type, range=product_range)
            assert all([benefit.name, benefit.description, str(benefit)])

    def test_proxy(self, product_range):
        for benefit_type, __ in Benefit.TYPE_CHOICES:
            benefit = Benefit(
                type=benefit_type, value=10, range=product_range, max_affected_items=1
            )
            proxy = benefit.proxy()
            assert benefit.type == proxy.type
            assert benefit.value == proxy.value
            assert benefit.range == proxy.range
            assert benefit.max_affected_items == proxy.max_affected_items


class TestBenefit(TestCase):
    def test_default_rounding(self):
        benefit = Benefit()

        decimal = Decimal(10.0570)

        self.assertEqual(
            benefit.round(decimal), decimal.quantize(Decimal("0.01"), ROUND_DOWN)
        )

    @override_settings(
        OSCAR_OFFER_ROUNDING_FUNCTION="tests._site.apps.offer.round.round_func"
    )
    @patch("tests._site.apps.offer.round.round_func")
    def test_round_uses_function_defined_in_OSCAR_OFFER_ROUNDING_FUNCTION(
        self, round_func_mock
    ):
        benefit = Benefit()

        decimal = Decimal(10.05)

        self.assertEqual(benefit.round(decimal), round_func_mock(decimal))
