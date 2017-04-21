from django.test import TestCase
from django.utils import six


from oscar.apps.offer.models import Benefit
from oscar.test import factories


class TestBenefitProxyModels(TestCase):

    def test_name_and_description(self):
        """
        Tests that the benefit proxy classes all return a name and
        description. Unfortunately, the current implementations means
        a valid range is required.
        This test became necessary because the complex name/description logic
        broke with the python_2_unicode_compatible decorator.
        """
        range = factories.RangeFactory()
        for type, __ in Benefit.TYPE_CHOICES:
            benefit = Benefit(type=type, range=range)
            self.assertTrue(all([
                benefit.name,
                benefit.description,
                six.text_type(benefit)]))
