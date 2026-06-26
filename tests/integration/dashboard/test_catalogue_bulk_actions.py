from decimal import Decimal

from django.test import TestCase

from oscar.core.loading import get_class, get_model
from oscar.test.factories import create_product, create_stockrecord
from oscar.test.utils import RequestFactory

Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")
ChildrenBulkActionForm = get_class(
    "dashboard.catalogue.forms", "ChildrenBulkActionForm"
)
SetChildrenPriceForm = get_class("dashboard.catalogue.forms", "SetChildrenPriceForm")
MakeProductsPublicAction = get_class(
    "dashboard.catalogue.bulk_actions", "MakeProductsPublicAction"
)
MakeProductsNonPublicAction = get_class(
    "dashboard.catalogue.bulk_actions", "MakeProductsNonPublicAction"
)
SetProductPriceAction = get_class(
    "dashboard.catalogue.bulk_actions", "SetProductPriceAction"
)


class TestChildrenBulkActionForm(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(structure="child", parent=self.parent)
        self.child2 = create_product(structure="child", parent=self.parent)
        self.qs = Product.objects.filter(parent=self.parent)

    def test_valid_single_selection(self):
        form = ChildrenBulkActionForm(
            data={"selected_products": [self.child1.pk]},
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertIn(self.child1, form.cleaned_data["selected_products"])
        self.assertNotIn(self.child2, form.cleaned_data["selected_products"])

    def test_valid_multiple_selection(self):
        form = ChildrenBulkActionForm(
            data={"selected_products": [self.child1.pk, self.child2.pk]},
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertIn(self.child1, form.cleaned_data["selected_products"])
        self.assertIn(self.child2, form.cleaned_data["selected_products"])

    def test_invalid_no_selection(self):
        form = ChildrenBulkActionForm(data={}, products_queryset=self.qs)
        self.assertFalse(form.is_valid())
        self.assertIn("selected_products", form.errors)
        self.assertIn("Select at least one product.", form.errors["selected_products"])

    def test_invalid_pk_outside_queryset(self):
        restricted_qs = Product.objects.filter(pk=self.child1.pk)
        form = ChildrenBulkActionForm(
            data={"selected_products": [self.child2.pk]},
            products_queryset=restricted_qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("selected_products", form.errors)

    def test_no_products_queryset_kwarg_rejects_all(self):
        form = ChildrenBulkActionForm(
            data={"selected_products": [self.child1.pk]},
        )
        self.assertFalse(form.is_valid())


class TestSetProductPriceForm(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(structure="child", parent=self.parent)
        self.child2 = create_product(structure="child", parent=self.parent)
        self.qs = Product.objects.filter(parent=self.parent)

    def test_valid_base_price_only(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk, self.child2.pk],
                "new_price": "9.99",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["new_price"], Decimal("9.99"))

    def test_valid_override_price_only(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk],
                f"price_{self.child1.pk}": "7.50",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_specific_prices()[self.child1.pk], Decimal("7.50"))

    def test_valid_mixed_base_and_override(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk, self.child2.pk],
                "new_price": "5.00",
                f"price_{self.child1.pk}": "12.00",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        specific = form.get_specific_prices()
        self.assertEqual(specific[self.child1.pk], Decimal("12.00"))
        self.assertNotIn(self.child2.pk, specific)

    def test_valid_increase_by_amount(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "increase_by_amount": "2.50",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())

    def test_valid_negative_increase_by_amount(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "increase_by_amount": "-2.50",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())

    def test_valid_increase_by_percentage(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "increase_by_percentage": "10",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())

    def test_valid_negative_increase_by_percentage(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "increase_by_percentage": "-10",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())

    def test_invalid_multiple_global_options(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "new_price": "5.00",
                "increase_by_amount": "1.00",
            },
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_invalid_no_price_for_selected(self):
        form = SetChildrenPriceForm(
            data={"selected_products": [self.child1.pk]},
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(f"price_{self.child1.pk}", form.errors)

    def test_invalid_negative_override(self):
        form = SetChildrenPriceForm(
            data={
                "selected_products": [self.child1.pk],
                f"price_{self.child1.pk}": "-1",
            },
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(f"price_{self.child1.pk}", form.errors)

    def test_invalid_negative_base_price(self):
        form = SetChildrenPriceForm(
            data={"selected_products": [self.child1.pk], "new_price": "-1"},
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("new_price", form.errors)

    def test_valid_zero_price(self):
        form = SetChildrenPriceForm(
            data={"selected_products": [self.child1.pk], "new_price": "0"},
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["new_price"], Decimal("0"))


class TestMakeProductsPublicAction(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(
            structure="child", parent=self.parent, is_public=False
        )
        self.child2 = create_product(
            structure="child", parent=self.parent, is_public=False
        )
        self.action = MakeProductsPublicAction()
        self.request = RequestFactory().get("/")

    def _make_form(self, children):
        qs = Product.objects.filter(pk__in=[c.pk for c in children])
        form = ChildrenBulkActionForm(
            data={"selected_products": [c.pk for c in children]},
            products_queryset=qs,
        )
        form.is_valid()
        return form

    def test_sets_is_public_true(self):
        form = self._make_form([self.child1, self.child2])
        self.action.execute(self.request, [self.child1, self.child2], form)
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertTrue(self.child1.is_public)
        self.assertTrue(self.child2.is_public)

    def test_returns_none(self):
        form = self._make_form([self.child1])
        result = self.action.execute(self.request, [self.child1], form)
        self.assertIsNone(result)


class TestMakeProductsNonPublicAction(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(
            structure="child", parent=self.parent, is_public=True
        )
        self.child2 = create_product(
            structure="child", parent=self.parent, is_public=True
        )
        self.action = MakeProductsNonPublicAction()
        self.request = RequestFactory().get("/")

    def _make_form(self, children):
        qs = Product.objects.filter(pk__in=[c.pk for c in children])
        form = ChildrenBulkActionForm(
            data={"selected_products": [c.pk for c in children]},
            products_queryset=qs,
        )
        form.is_valid()
        return form

    def test_sets_is_public_false(self):
        form = self._make_form([self.child1, self.child2])
        self.action.execute(self.request, [self.child1, self.child2], form)
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertFalse(self.child1.is_public)
        self.assertFalse(self.child2.is_public)

    def test_returns_none(self):
        form = self._make_form([self.child1])
        result = self.action.execute(self.request, [self.child1], form)
        self.assertIsNone(result)


class TestSetProductPriceAction(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(structure="child", parent=self.parent)
        self.child2 = create_product(structure="child", parent=self.parent)
        self.sr1 = create_stockrecord(self.child1, price=Decimal("5.00"))
        self.sr2 = create_stockrecord(self.child2, price=Decimal("5.00"))
        self.action = SetProductPriceAction()
        self.request = RequestFactory().get("/")

    def _make_form(self, data):
        qs = Product.objects.filter(pk__in=[self.child1.pk, self.child2.pk])
        form = SetChildrenPriceForm(data=data, products_queryset=qs)
        form.is_valid()
        return form

    def _objects(self, form):
        return list(form.cleaned_data["selected_products"])

    def test_base_price_updates_all(self):
        form = self._make_form(
            {
                "selected_products": [self.child1.pk, self.child2.pk],
                "new_price": "12.50",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        self.sr2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("12.50"))
        self.assertEqual(self.sr2.price, Decimal("12.50"))

    def test_per_variant_override(self):
        form = self._make_form(
            {
                "selected_products": [self.child1.pk, self.child2.pk],
                "new_price": "10.00",
                f"price_{self.child1.pk}": "20.00",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        self.sr2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("20.00"))
        self.assertEqual(self.sr2.price, Decimal("10.00"))

    def test_distinct_per_variant_prices(self):
        form = self._make_form(
            {
                "selected_products": [self.child1.pk, self.child2.pk],
                f"price_{self.child1.pk}": "3.00",
                f"price_{self.child2.pk}": "7.00",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        self.sr2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("3.00"))
        self.assertEqual(self.sr2.price, Decimal("7.00"))

    def test_increase_by_amount(self):
        form = self._make_form(
            {
                "selected_products": [self.child1.pk, self.child2.pk],
                "increase_by_amount": "3.00",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        self.sr2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("8.00"))
        self.assertEqual(self.sr2.price, Decimal("8.00"))

    def test_decrease_by_amount_clamps_to_zero(self):
        form = self._make_form(
            {
                "selected_products": [self.child1.pk],
                "increase_by_amount": "-99.00",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("0.00"))

    def test_increase_by_percentage(self):
        form = self._make_form(
            {
                "selected_products": [self.child1.pk, self.child2.pk],
                "increase_by_percentage": "20",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        self.sr2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("6.00"))
        self.assertEqual(self.sr2.price, Decimal("6.00"))

    def test_decrease_by_percentage_clamps_to_zero(self):
        form = self._make_form(
            {
                "selected_products": [self.child1.pk],
                "increase_by_percentage": "-200",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("0.00"))

    def test_override_takes_precedence_over_increase(self):
        form = self._make_form(
            {
                "selected_products": [self.child1.pk, self.child2.pk],
                "increase_by_amount": "3.00",
                f"price_{self.child1.pk}": "99.00",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        self.sr2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("99.00"))
        self.assertEqual(self.sr2.price, Decimal("8.00"))

    def test_only_updates_stockrecords_for_selected_products(self):
        standalone = create_product()
        sr_standalone = create_stockrecord(standalone, price=Decimal("5.00"))
        form = self._make_form(
            {
                "selected_products": [self.child1.pk],
                "new_price": "12.50",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        sr_standalone.refresh_from_db()
        self.assertEqual(sr_standalone.price, Decimal("5.00"))

    def test_partner_filter_only_updates_selected_partner(self):
        sr1_p2 = create_stockrecord(
            self.child1, price=Decimal("5.00"), partner_name="Partner 2"
        )
        form = self._make_form(
            {
                "selected_products": [self.child1.pk],
                "new_price": "20.00",
                "partners": [self.sr1.partner.pk],
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        sr1_p2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("20.00"))
        self.assertEqual(sr1_p2.price, Decimal("5.00"))

    def test_empty_partner_filter_updates_all_partners(self):
        sr1_p2 = create_stockrecord(
            self.child1, price=Decimal("5.00"), partner_name="Partner 2"
        )
        form = self._make_form(
            {
                "selected_products": [self.child1.pk],
                "new_price": "20.00",
            }
        )
        self.action.execute(self.request, self._objects(form), form)
        self.sr1.refresh_from_db()
        sr1_p2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("20.00"))
        self.assertEqual(sr1_p2.price, Decimal("20.00"))

    def test_returns_none(self):
        form = self._make_form(
            {"selected_products": [self.child1.pk], "new_price": "9.00"}
        )
        result = self.action.execute(self.request, self._objects(form), form)
        self.assertIsNone(result)
