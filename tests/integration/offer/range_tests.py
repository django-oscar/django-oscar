from django.conf import settings
from django.test import TestCase

from oscar.apps.offer import models
from oscar.test.factories import create_product


class TestWholeSiteRangeWithGlobalBlacklist(TestCase):

    def setUp(self):
        self.range = models.Range(
            name="All products", includes_all_products=True)

    def tearDown(self):
        settings.OSCAR_OFFER_BLACKLIST_PRODUCT = None

    def test_blacklisting_prevents_products_being_in_range(self):
        settings.OSCAR_OFFER_BLACKLIST_PRODUCT = lambda p: True
        prod = create_product()
        self.assertFalse(self.range.contains_product(prod))

    def test_blacklisting_can_use_product_class(self):
        settings.OSCAR_OFFER_BLACKLIST_PRODUCT = (
            lambda p: p.get_product_class().name == 'giftcard')
        prod = create_product(product_class="giftcard")
        self.assertFalse(self.range.contains_product(prod))

    def test_blacklisting_doesnt_exlude_everything(self):
        settings.OSCAR_OFFER_BLACKLIST_PRODUCT = (
            lambda p: p.get_product_class().name == 'giftcard')
        prod = create_product(product_class="book")
        self.assertTrue(self.range.contains_product(prod))


class TestWholeSiteRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.prod = create_product()

    def test_all_products_range(self):
        self.assertTrue(self.range.contains_product(self.prod))

    def test_all_products_range_with_exception(self):
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))

    def test_whitelisting(self):
        self.range.add_product(self.prod)
        self.assertTrue(self.range.contains_product(self.prod))

    def test_blacklisting(self):
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))


class TestPartialRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=False)
        self.prod = create_product()

    def test_empty_list(self):
        self.assertFalse(self.range.contains_product(self.prod))

    def test_included_classes(self):
        self.range.classes.add(self.prod.get_product_class())
        self.assertTrue(self.range.contains_product(self.prod))

    def test_included_class_with_exception(self):
        self.range.classes.add(self.prod.get_product_class())
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))
