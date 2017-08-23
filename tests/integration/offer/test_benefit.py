import pytest

from django.utils import six


from oscar.apps.offer.models import Benefit
from oscar.test import factories


@pytest.fixture
def range():
    return factories.RangeFactory()


@pytest.mark.django_db
class TestBenefitProxyModels(object):
    """

    https://docs.djangoproject.com/en/1.11/topics/db/models/#proxy-models

    """

    def test_name_and_description(self, range):
        """
        Tests that the benefit proxy classes all return a name and
        description. Unfortunately, the current implementations means
        a valid range is required.
        This test became necessary because the complex name/description logic
        broke with the python_2_unicode_compatible decorator.
        """
        for benefit_type, __ in Benefit.TYPE_CHOICES:
            benefit = Benefit(type=benefit_type, range=range)
            assert all([
                benefit.name,
                benefit.description,
                six.text_type(benefit)])

    def test_proxy(self, range):
        for benefit_type, __ in Benefit.TYPE_CHOICES:
            benefit = Benefit(
                type=benefit_type, value=10, range=range, max_affected_items=1)
            proxy = benefit.proxy()
            assert benefit.type == proxy.type
            assert benefit.value == proxy.value
            assert benefit.range == proxy.range
            assert benefit.max_affected_items == proxy.max_affected_items
