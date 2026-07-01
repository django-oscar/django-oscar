from django.test import TestCase

from oscar.apps.catalogue.models import Product
from oscar.apps.partner import strategy
from oscar.test import factories


class TestUseFirstStockRecordMixin(TestCase):
    def setUp(self):
        self.product = factories.create_product()
        self.mixin = strategy.UseFirstStockRecord()

    def test_selects_first_stockrecord_for_product(self):
        stockrecord = factories.create_stockrecord(self.product)
        selected = self.mixin.select_stockrecord(self.product)
        self.assertEqual(selected.id, stockrecord.id)

    def test_returns_none_when_no_stock_records(self):
        self.assertIsNone(self.mixin.select_stockrecord(self.product))

    def test_does_not_generate_additional_query_when_passed_product_from_base_queryset(
        self,
    ):
        product = Product.objects.base_queryset().first()
        # Regression test for https://github.com/django-oscar/django-oscar/issues/3875
        # If passed a product from a queryset annotated by base_queryset, then
        # the selector should not trigger any additional database queries because
        # it should rely on the prefetched stock records.
        with self.assertNumQueries(0):
            self.mixin.select_stockrecord(product)
