from decimal import Decimal

from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.test import TestCase

from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    PartnerFactory,
    UserFactory,
    create_product,
    create_stockrecord,
)
from oscar.test.utils import RequestFactory

Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")
Partner = get_model("partner", "Partner")
ProductBulkActionForm = get_class("dashboard.catalogue.forms", "ProductBulkActionForm")
SetProductPriceForm = get_class("dashboard.catalogue.forms", "SetProductPriceForm")
MakeProductsPublicAction = get_class(
    "dashboard.catalogue.bulk_actions", "MakeProductsPublicAction"
)
MakeProductsNonPublicAction = get_class(
    "dashboard.catalogue.bulk_actions", "MakeProductsNonPublicAction"
)
SetProductPriceAction = get_class(
    "dashboard.catalogue.bulk_actions", "SetProductPriceAction"
)


class TestProductBulkActionForm(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(structure="child", parent=self.parent)
        self.child2 = create_product(structure="child", parent=self.parent)
        self.qs = Product.objects.filter(parent=self.parent)

    def test_valid_single_selection(self):
        form = ProductBulkActionForm(
            data={"selected_products": [self.child1.pk]},
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertIn(self.child1, form.cleaned_data["selected_products"])
        self.assertNotIn(self.child2, form.cleaned_data["selected_products"])

    def test_valid_multiple_selection(self):
        form = ProductBulkActionForm(
            data={"selected_products": [self.child1.pk, self.child2.pk]},
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertIn(self.child1, form.cleaned_data["selected_products"])
        self.assertIn(self.child2, form.cleaned_data["selected_products"])

    def test_invalid_no_selection(self):
        form = ProductBulkActionForm(data={}, products_queryset=self.qs)
        self.assertFalse(form.is_valid())
        self.assertIn("selected_products", form.errors)
        self.assertIn("Select at least one product.", form.errors["selected_products"])

    def test_invalid_pk_outside_queryset(self):
        restricted_qs = Product.objects.filter(pk=self.child1.pk)
        form = ProductBulkActionForm(
            data={"selected_products": [self.child2.pk]},
            products_queryset=restricted_qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("selected_products", form.errors)

    def test_no_products_queryset_kwarg_rejects_all(self):
        form = ProductBulkActionForm(
            data={"selected_products": [self.child1.pk]},
        )
        self.assertFalse(form.is_valid())


class TestSetProductPriceForm(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(structure="child", parent=self.parent)
        self.child2 = create_product(structure="child", parent=self.parent)
        create_stockrecord(self.child1, price=Decimal("5.00"))
        create_stockrecord(self.child2, price=Decimal("5.00"))
        # Both stockrecords share the same (default) partner; partners is required.
        self.partner = self.child1.stockrecords.first().partner
        self.qs = Product.objects.filter(parent=self.parent)

    def test_valid_base_price_only(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk, self.child2.pk],
                "partners": [self.partner.pk],
                "new_price": "9.99",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["new_price"], Decimal("9.99"))

    def test_valid_override_price_only(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                f"price_{self.child1.pk}": "7.50",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_specific_prices()[self.child1.pk], Decimal("7.50"))

    def test_valid_mixed_base_and_override(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk, self.child2.pk],
                "partners": [self.partner.pk],
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
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "increase_by_amount": "2.50",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())

    def test_valid_negative_increase_by_amount(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "increase_by_amount": "-2.50",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())

    def test_valid_increase_by_percentage(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "increase_by_percentage": "10",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())

    def test_valid_negative_increase_by_percentage(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "increase_by_percentage": "-10",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())

    def test_invalid_multiple_global_options(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "new_price": "5.00",
                "increase_by_amount": "1.00",
            },
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_invalid_no_price_for_selected(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
            },
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_invalid_negative_override(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                f"price_{self.child1.pk}": "-1",
            },
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(f"price_{self.child1.pk}", form.errors)

    def test_invalid_negative_base_price(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "new_price": "-1",
            },
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("new_price", form.errors)

    def test_valid_zero_price(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "new_price": "0",
            },
            products_queryset=self.qs,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["new_price"], Decimal("0"))

    def test_invalid_without_partners(self):
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child1.pk],
                "new_price": "9.99",
            },
            products_queryset=self.qs,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("partners", form.errors)

    def test_partners_field_is_required(self):
        form = SetProductPriceForm(products_queryset=self.qs)
        self.assertTrue(form.fields["partners"].required)

    def test_single_partner_is_preselected(self):
        # setUp only ever creates stockrecords under one shared partner, so
        # there's no real choice to make: it's preselected automatically.
        form = SetProductPriceForm(products_queryset=self.qs)
        self.assertEqual(list(form.fields["partners"].initial), [self.partner])

    def test_multiple_partners_are_not_preselected(self):
        # With a genuine choice between partners, nothing is preselected
        # (opt in).
        create_stockrecord(self.child2, price=Decimal("5.00"), partner_name="Partner 2")
        form = SetProductPriceForm(products_queryset=self.qs)
        self.assertFalse(form.fields["partners"].initial)


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
        # A staff user: these tests exercise the general toggle mechanics,
        # not partner scoping (see TestSetProductsPublicStatusPartnerIsolation).
        self.request = RequestFactory().get("/", user=UserFactory(is_staff=True))

    def _qs(self, children):
        return Product.objects.filter(pk__in=[c.pk for c in children])

    def _make_form(self, children):
        form = ProductBulkActionForm(
            data={"selected_products": [c.pk for c in children]},
            products_queryset=self._qs(children),
        )
        form.is_valid()
        return form

    def test_sets_is_public_true(self):
        children = [self.child1, self.child2]
        form = self._make_form(children)
        self.action.execute(self.request, self._qs(children), form)
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertTrue(self.child1.is_public)
        self.assertTrue(self.child2.is_public)

    def test_returns_none(self):
        form = self._make_form([self.child1])
        result = self.action.execute(self.request, self._qs([self.child1]), form)
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
        # A staff user: these tests exercise the general toggle mechanics,
        # not partner scoping (see TestSetProductsPublicStatusPartnerIsolation).
        self.request = RequestFactory().get("/", user=UserFactory(is_staff=True))

    def _qs(self, children):
        return Product.objects.filter(pk__in=[c.pk for c in children])

    def _make_form(self, children):
        form = ProductBulkActionForm(
            data={"selected_products": [c.pk for c in children]},
            products_queryset=self._qs(children),
        )
        form.is_valid()
        return form

    def test_sets_is_public_false(self):
        children = [self.child1, self.child2]
        form = self._make_form(children)
        self.action.execute(self.request, self._qs(children), form)
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertFalse(self.child1.is_public)
        self.assertFalse(self.child2.is_public)

    def test_returns_none(self):
        form = self._make_form([self.child1])
        result = self.action.execute(self.request, self._qs([self.child1]), form)
        self.assertIsNone(result)


class TestSetProductsPublicStatusPartnerIsolation(TestCase):
    """A non-staff partner user must only be able to change the public
    status of products where at least one stockrecord is their own."""

    def setUp(self):
        self.partner_own = PartnerFactory(name="Own Partner")
        self.non_staff_user = UserFactory(is_staff=False)
        self.partner_own.users.add(self.non_staff_user)

        self.standalone_own = create_product(structure="standalone", is_public=False)
        create_stockrecord(self.standalone_own, partner_name="Own Partner")

        self.standalone_foreign = create_product(
            structure="standalone", is_public=False
        )
        create_stockrecord(self.standalone_foreign, partner_name="Foreign Partner")

        self.parent_with_own_child = create_product(structure="parent", is_public=False)
        self.child_own = create_product(
            structure="child", parent=self.parent_with_own_child, is_public=False
        )
        create_stockrecord(self.child_own, partner_name="Own Partner")

        self.parent_foreign_only = create_product(structure="parent", is_public=False)
        self.child_foreign = create_product(
            structure="child", parent=self.parent_foreign_only, is_public=False
        )
        create_stockrecord(self.child_foreign, partner_name="Foreign Partner")

        self.action = MakeProductsPublicAction()

    def _qs(self, products):
        return Product.objects.filter(pk__in=[p.pk for p in products])

    def _make_form(self, products):
        form = ProductBulkActionForm(
            data={"selected_products": [p.pk for p in products]},
            products_queryset=self._qs(products),
        )
        form.is_valid()
        return form

    def test_non_staff_only_updates_own_partners_standalone(self):
        products = [self.standalone_own, self.standalone_foreign]
        request = RequestFactory().get("/", user=self.non_staff_user)
        self.action.execute(request, self._qs(products), self._make_form(products))

        self.standalone_own.refresh_from_db()
        self.standalone_foreign.refresh_from_db()
        self.assertTrue(self.standalone_own.is_public)
        self.assertFalse(self.standalone_foreign.is_public)

    def test_non_staff_can_update_parent_via_own_child_stockrecord(self):
        request = RequestFactory().get("/", user=self.non_staff_user)
        self.action.execute(
            request,
            self._qs([self.parent_with_own_child]),
            self._make_form([self.parent_with_own_child]),
        )
        self.parent_with_own_child.refresh_from_db()
        self.assertTrue(self.parent_with_own_child.is_public)

    def test_non_staff_cannot_update_parent_with_only_foreign_children(self):
        request = RequestFactory().get("/", user=self.non_staff_user)
        self.action.execute(
            request,
            self._qs([self.parent_foreign_only]),
            self._make_form([self.parent_foreign_only]),
        )
        self.parent_foreign_only.refresh_from_db()
        self.assertFalse(self.parent_foreign_only.is_public)

    def test_staff_updates_regardless_of_partner(self):
        staff_user = UserFactory(is_staff=True)
        products = [self.standalone_own, self.standalone_foreign]
        request = RequestFactory().get("/", user=staff_user)
        self.action.execute(request, self._qs(products), self._make_form(products))

        self.standalone_own.refresh_from_db()
        self.standalone_foreign.refresh_from_db()
        self.assertTrue(self.standalone_own.is_public)
        self.assertTrue(self.standalone_foreign.is_public)


class TestSetProductPriceAction(TestCase):
    def setUp(self):
        self.parent = create_product(structure="parent")
        self.child1 = create_product(structure="child", parent=self.parent)
        self.child2 = create_product(structure="child", parent=self.parent)
        self.sr1 = create_stockrecord(self.child1, price=Decimal("5.00"))
        self.sr2 = create_stockrecord(self.child2, price=Decimal("5.00"))
        self.action = SetProductPriceAction()
        # A staff user: these tests exercise the general price-update
        # mechanics, not partner scoping (see TestSetProductPriceActionPartnerIsolation).
        staff_user = UserFactory(is_staff=True)
        self.request = RequestFactory().get("/", user=staff_user)

    def _make_form(self, data):
        qs = Product.objects.filter(pk__in=[self.child1.pk, self.child2.pk])
        # partners is required; these tests exercise pricing mechanics, not
        # partner scoping, so default it to the shared partner unless a test
        # supplies its own.
        data.setdefault("partners", [self.sr1.partner.pk])
        form = SetProductPriceForm(data=data, products_queryset=qs)
        form.is_valid()
        return form

    def _objects(self, form):
        return form.cleaned_data["selected_products"]

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

    def test_no_partners_raises(self):
        # partners is required on the form; execute() must never silently
        # fall back to "update every partner" when it's missing.
        form = self._make_form(
            {
                "selected_products": [self.child1.pk],
                "new_price": "20.00",
                "partners": [],
            }
        )
        with self.assertRaises(SuspiciousOperation):
            self.action.execute(self.request, self._objects(form), form)

    def test_returns_none(self):
        form = self._make_form(
            {"selected_products": [self.child1.pk], "new_price": "9.00"}
        )
        result = self.action.execute(self.request, self._objects(form), form)
        self.assertIsNone(result)


class TestSetProductPriceActionPartnerIsolation(TestCase):
    """A non-staff partner user must never be able to update another
    partner's stockrecords, however the request is constructed."""

    def setUp(self):
        self.partner_a = PartnerFactory(name="Partner A")
        self.partner_b = PartnerFactory(name="Partner B")
        self.non_staff_user = UserFactory(is_staff=False)
        self.partner_a.users.add(self.non_staff_user)

        self.parent = create_product(structure="parent")
        self.child = create_product(structure="child", parent=self.parent)
        self.sr_a = create_stockrecord(
            self.child, price=Decimal("5.00"), partner_name="Partner A"
        )
        self.sr_b = create_stockrecord(
            self.child, price=Decimal("5.00"), partner_name="Partner B"
        )

        self.action = SetProductPriceAction()

    def _make_form(self, data, products_queryset=None):
        qs = products_queryset or Product.objects.filter(pk=self.child.pk)
        form = SetProductPriceForm(
            data=data, products_queryset=qs, user=self.non_staff_user
        )
        form.is_valid()
        return form

    def test_partner_choices_exclude_other_partners_stockrecord(self):
        form = self._make_form({"selected_products": [self.child.pk]})
        choices = set(form.fields["partners"].queryset)
        self.assertIn(self.partner_a, choices)
        self.assertNotIn(self.partner_b, choices)

    def test_submitting_foreign_partner_pk_is_rejected_by_form(self):
        form = self._make_form(
            {
                "selected_products": [self.child.pk],
                "partners": [self.partner_b.pk],
                "new_price": "20.00",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("partners", form.errors)

    def test_execute_never_updates_other_partners_stockrecord(self):
        # Even if cleaned_data somehow carried the foreign partner (e.g. a
        # bypassed/forged form), execute() must not trust it.
        form = self._make_form(
            {
                "selected_products": [self.child.pk],
                "partners": [self.partner_a.pk],
                "new_price": "20.00",
            }
        )
        self.assertTrue(form.is_valid())
        form.cleaned_data["partners"] = Partner.objects.filter(
            pk__in=[self.partner_a.pk, self.partner_b.pk]
        )

        request = RequestFactory().get("/", user=self.non_staff_user)
        self.action.execute(request, Product.objects.filter(pk=self.child.pk), form)

        self.sr_a.refresh_from_db()
        self.sr_b.refresh_from_db()
        self.assertEqual(self.sr_a.price, Decimal("20.00"))
        self.assertEqual(self.sr_b.price, Decimal("5.00"))

    def test_execute_raises_when_no_partners_provided(self):
        # partners is required on the form; execute() must never silently
        # default to "just my own partners" (or worse, "every partner").
        form = self._make_form(
            {
                "selected_products": [self.child.pk],
                "new_price": "20.00",
            }
        )
        request = RequestFactory().get("/", user=self.non_staff_user)
        with self.assertRaises(SuspiciousOperation):
            self.action.execute(request, Product.objects.filter(pk=self.child.pk), form)

        self.sr_a.refresh_from_db()
        self.sr_b.refresh_from_db()
        self.assertEqual(self.sr_a.price, Decimal("5.00"))
        self.assertEqual(self.sr_b.price, Decimal("5.00"))

    def test_execute_raises_when_selection_intersects_to_nothing(self):
        # A non-staff user submitting only a foreign partner must raise,
        # never silently fall back to updating every partner.
        form = self._make_form(
            {
                "selected_products": [self.child.pk],
                "partners": [self.partner_b.pk],
                "new_price": "20.00",
            },
        )
        form.cleaned_data["partners"] = Partner.objects.filter(pk=self.partner_b.pk)

        request = RequestFactory().get("/", user=self.non_staff_user)
        with self.assertRaises(PermissionDenied):
            self.action.execute(request, Product.objects.filter(pk=self.child.pk), form)

        self.sr_a.refresh_from_db()
        self.sr_b.refresh_from_db()
        self.assertEqual(self.sr_a.price, Decimal("5.00"))
        self.assertEqual(self.sr_b.price, Decimal("5.00"))

    def test_staff_user_can_update_both_partners(self):
        staff_user = UserFactory(is_staff=True)
        form = SetProductPriceForm(
            data={
                "selected_products": [self.child.pk],
                "partners": [self.partner_a.pk, self.partner_b.pk],
                "new_price": "20.00",
            },
            products_queryset=Product.objects.filter(pk=self.child.pk),
            user=staff_user,
        )
        self.assertTrue(form.is_valid())

        request = RequestFactory().get("/", user=staff_user)
        self.action.execute(request, Product.objects.filter(pk=self.child.pk), form)

        self.sr_a.refresh_from_db()
        self.sr_b.refresh_from_db()
        self.assertEqual(self.sr_a.price, Decimal("20.00"))
        self.assertEqual(self.sr_b.price, Decimal("20.00"))
