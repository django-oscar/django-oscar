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
MakeChildrenPublicAction = get_class(
    "dashboard.catalogue.bulk_actions", "MakeChildrenPublicAction"
)
MakeChildrenNonPublicAction = get_class(
    "dashboard.catalogue.bulk_actions", "MakeChildrenNonPublicAction"
)
SetChildrenPriceAction = get_class(
    "dashboard.catalogue.bulk_actions", "SetChildrenPriceAction"
)


class TestChildrenBulkActionForm(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(structure="child", parent=self.parent)
        self.child2 = create_product(structure="child", parent=self.parent)
        self.qs = Product.objects.filter(parent=self.parent)

    def test_valid_single_selection(self):
        form = ChildrenBulkActionForm(
            data={"selected_children": [self.child1.pk]},
            children_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertIn(self.child1, form.cleaned_data["selected_children"])
        self.assertNotIn(self.child2, form.cleaned_data["selected_children"])

    def test_valid_multiple_selection(self):
        form = ChildrenBulkActionForm(
            data={"selected_children": [self.child1.pk, self.child2.pk]},
            children_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertIn(self.child1, form.cleaned_data["selected_children"])
        self.assertIn(self.child2, form.cleaned_data["selected_children"])

    def test_invalid_no_selection(self):
        form = ChildrenBulkActionForm(data={}, children_queryset=self.qs)
        self.assertFalse(form.is_valid())
        self.assertIn("selected_children", form.errors)
        self.assertIn(
            "Select at least one child product.", form.errors["selected_children"]
        )

    def test_invalid_pk_outside_queryset(self):
        restricted_qs = Product.objects.filter(pk=self.child1.pk)
        form = ChildrenBulkActionForm(
            data={"selected_children": [self.child2.pk]},
            children_queryset=restricted_qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("selected_children", form.errors)

    def test_no_children_queryset_kwarg_rejects_all(self):
        form = ChildrenBulkActionForm(
            data={"selected_children": [self.child1.pk]},
        )
        self.assertFalse(form.is_valid())


class TestSetChildrenPriceForm(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child = create_product(structure="child", parent=self.parent)
        self.qs = Product.objects.filter(parent=self.parent)

    def test_valid_with_price(self):
        form = SetChildrenPriceForm(
            data={"selected_children": [self.child.pk], "new_price": "9.99"},
            children_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["new_price"], Decimal("9.99"))

    def test_invalid_missing_price(self):
        form = SetChildrenPriceForm(
            data={"selected_children": [self.child.pk]},
            children_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("new_price", form.errors)

    def test_invalid_negative_price(self):
        form = SetChildrenPriceForm(
            data={"selected_children": [self.child.pk], "new_price": "-1"},
            children_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("new_price", form.errors)

    def test_valid_zero_price(self):
        form = SetChildrenPriceForm(
            data={"selected_children": [self.child.pk], "new_price": "0"},
            children_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["new_price"], Decimal("0"))


class TestMakeChildrenPublicAction(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(
            structure="child", parent=self.parent, is_public=False
        )
        self.child2 = create_product(
            structure="child", parent=self.parent, is_public=False
        )
        self.action = MakeChildrenPublicAction()
        self.request = RequestFactory().get("/")

    def test_sets_is_public_true(self):
        self.action.execute(self.request, [self.child1.pk, self.child2.pk], form=None)
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertTrue(self.child1.is_public)
        self.assertTrue(self.child2.is_public)

    def test_ignores_non_child_structure(self):
        standalone = create_product(is_public=False)
        self.action.execute(self.request, [self.child1.pk, standalone.pk], form=None)
        standalone.refresh_from_db()
        self.assertFalse(standalone.is_public)

    def test_returns_none(self):
        result = self.action.execute(self.request, [self.child1.pk], form=None)
        self.assertIsNone(result)


class TestMakeChildrenNonPublicAction(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(
            structure="child", parent=self.parent, is_public=True
        )
        self.child2 = create_product(
            structure="child", parent=self.parent, is_public=True
        )
        self.action = MakeChildrenNonPublicAction()
        self.request = RequestFactory().get("/")

    def test_sets_is_public_false(self):
        self.action.execute(self.request, [self.child1.pk, self.child2.pk], form=None)
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertFalse(self.child1.is_public)
        self.assertFalse(self.child2.is_public)

    def test_ignores_parent_structure(self):
        self.action.execute(self.request, [self.child1.pk, self.parent.pk], form=None)
        self.parent.refresh_from_db()
        self.assertTrue(self.parent.is_public)

    def test_returns_none(self):
        result = self.action.execute(self.request, [self.child1.pk], form=None)
        self.assertIsNone(result)


class TestSetChildrenPriceAction(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(structure="child", parent=self.parent)
        self.child2 = create_product(structure="child", parent=self.parent)
        self.sr1 = create_stockrecord(self.child1, price=Decimal("5.00"))
        self.sr2 = create_stockrecord(self.child2, price=Decimal("5.00"))
        self.action = SetChildrenPriceAction()
        self.request = RequestFactory().get("/")

        qs = Product.objects.filter(pk__in=[self.child1.pk, self.child2.pk])
        self.form = SetChildrenPriceForm(
            data={
                "selected_children": [self.child1.pk, self.child2.pk],
                "new_price": "12.50",
            },
            children_queryset=qs,
        )
        self.form.is_valid()

    def test_updates_stockrecord_price(self):
        self.action.execute(self.request, [self.child1.pk, self.child2.pk], self.form)
        self.sr1.refresh_from_db()
        self.sr2.refresh_from_db()
        self.assertEqual(self.sr1.price, Decimal("12.50"))
        self.assertEqual(self.sr2.price, Decimal("12.50"))

    def test_ignores_non_child_stockrecords(self):
        standalone = create_product()
        sr_standalone = create_stockrecord(standalone, price=Decimal("5.00"))
        self.action.execute(self.request, [self.child1.pk, standalone.pk], self.form)
        sr_standalone.refresh_from_db()
        self.assertEqual(sr_standalone.price, Decimal("5.00"))

    def test_returns_none(self):
        result = self.action.execute(self.request, [self.child1.pk], self.form)
        self.assertIsNone(result)
