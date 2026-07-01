import unittest.mock as mock

from django.test import TestCase

from oscar.apps.catalogue.models import ProductClass
from oscar.apps.dashboard.catalogue.forms import StockRecordForm


class StockRecordFormTextCase(TestCase):
    def test_stockrecord_form_has_all_fields_when_tracking_stock(self):
        product_with_stock_tracking = ProductClass()
        henk = mock.Mock(is_staff=True)

        form = StockRecordForm(product_with_stock_tracking, henk)
        form_field_names = [f.name for f in form.visible_fields()]

        self.assertIn(
            "num_in_stock",
            form_field_names,
            "num_in_stock should be a field in the form",
        )
        self.assertIn(
            "low_stock_threshold",
            form_field_names,
            "low_stock_threshold should be a field in the form",
        )

    def test_stockrecord_form_has_less_fields_when_not_tracking_stock(self):
        product_with_no_stock_tracking = ProductClass(track_stock=False)
        henk = mock.Mock(is_staff=True)

        form = StockRecordForm(product_with_no_stock_tracking, henk)
        form_field_names = [f.name for f in form.visible_fields()]

        self.assertNotIn(
            "num_in_stock",
            form_field_names,
            "num_in_stock should NOT be a field in the form",
        )
        self.assertNotIn(
            "low_stock_threshold",
            form_field_names,
            "low_stock_threshold should NOT be a field in the form",
        )
