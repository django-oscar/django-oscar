from decimal import Decimal

from django.urls import reverse

from oscar.core.loading import get_class
from oscar.test.factories import create_product, create_stockrecord
from oscar.test.testcases import WebTestCase

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class ChildrenBulkActionTests(WebTestCase):
    is_staff = True
    csrf_checks = False
    permissions = DashboardPermission.get("catalogue", "view_product", "change_product")

    def setUp(self):
        super().setUp()
        self.parent = create_product(structure="parent")
        self.child1 = create_product(
            structure="child", parent=self.parent, is_public=False
        )
        self.child2 = create_product(
            structure="child", parent=self.parent, is_public=False
        )
        create_stockrecord(self.child1, price=Decimal("5.00"))
        create_stockrecord(self.child2, price=Decimal("5.00"))

    def _seed_session(self, action):
        return self.post(
            reverse("dashboard:catalogue-product-list"),
            params={"action": action, "selected_product": [self.parent.pk]},
        )

    def _intermediate_url(self):
        return reverse("dashboard:catalogue-product-children-bulk-action")


class TestMakeChildrenPublicFlow(ChildrenBulkActionTests):
    def test_list_post_redirects_to_intermediate(self):
        response = self._seed_session("make_children_public")
        self.assertIsRedirect(response, self._intermediate_url())

    def test_get_intermediate_view_renders_form(self):
        self._seed_session("make_children_public")
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        self.assertInContext(page, "form")
        self.assertInContext(page, "parents_with_children")
        parents = list(page.context["parents_with_children"])
        self.assertIn(self.parent, parents)

    def test_submit_makes_children_public(self):
        self._seed_session("make_children_public")
        response = self.post(
            self._intermediate_url(),
            params={"selected_children": [self.child1.pk, self.child2.pk]},
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertTrue(self.child1.is_public)
        self.assertTrue(self.child2.is_public)

    def test_session_cleared_after_submit(self):
        self._seed_session("make_children_public")
        self.post(
            self._intermediate_url(),
            params={"selected_children": [self.child1.pk]},
        )
        response = self.get(self._intermediate_url())
        self.assertIsRedirect(response)


class TestMakeChildrenNonPublicFlow(ChildrenBulkActionTests):
    def setUp(self):
        super().setUp()
        self.child1.is_public = True
        self.child1.save()
        self.child2.is_public = True
        self.child2.save()

    def test_submit_makes_children_non_public(self):
        self._seed_session("make_children_non_public")
        response = self.post(
            self._intermediate_url(),
            params={"selected_children": [self.child1.pk, self.child2.pk]},
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertFalse(self.child1.is_public)
        self.assertFalse(self.child2.is_public)

    def test_empty_selection_rerenders_with_error(self):
        self._seed_session("make_children_non_public")
        page = self.post(self._intermediate_url(), params={})
        self.assertIsOk(page)
        form = page.context["form"]
        self.assertIn("selected_children", form.errors)
        self.assertIn("Select at least one variant.", form.errors["selected_children"])


class TestSetChildrenPriceFlow(ChildrenBulkActionTests):
    def test_list_post_redirects_to_intermediate(self):
        response = self._seed_session("set_children_price")
        self.assertIsRedirect(response, self._intermediate_url())

    def test_get_shows_price_form(self):
        self._seed_session("set_children_price")
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        form = page.context["form"]
        self.assertIn("new_price", form.fields)

    def test_submit_valid_base_price(self):
        self._seed_session("set_children_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_children": [self.child1.pk, self.child2.pk],
                "new_price": "19.99",
            },
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        sr1 = self.child1.stockrecords.first()
        sr2 = self.child2.stockrecords.first()
        sr1.refresh_from_db()
        sr2.refresh_from_db()
        self.assertEqual(sr1.price, Decimal("19.99"))
        self.assertEqual(sr2.price, Decimal("19.99"))

    def test_submit_valid_override_prices(self):
        self._seed_session("set_children_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_children": [self.child1.pk, self.child2.pk],
                f"price_{self.child1.pk}": "11.00",
                f"price_{self.child2.pk}": "22.00",
            },
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        sr1 = self.child1.stockrecords.first()
        sr2 = self.child2.stockrecords.first()
        sr1.refresh_from_db()
        sr2.refresh_from_db()
        self.assertEqual(sr1.price, Decimal("11.00"))
        self.assertEqual(sr2.price, Decimal("22.00"))

    def test_variants_without_stockrecord_are_excluded(self):
        child_no_sr = create_product(structure="child", parent=self.parent)
        self._seed_session("set_children_price")
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        form = page.context["form"]
        child_pks = [c.pk for c in form.fields["selected_children"].queryset]
        self.assertIn(self.child1.pk, child_pks)
        self.assertIn(self.child2.pk, child_pks)
        self.assertNotIn(child_no_sr.pk, child_pks)

    def test_submit_increase_by_amount(self):
        self._seed_session("set_children_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_children": [self.child1.pk, self.child2.pk],
                "increase_by_amount": "2.00",
            },
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.stockrecords.first().refresh_from_db()
        self.child2.stockrecords.first().refresh_from_db()
        self.assertEqual(self.child1.stockrecords.first().price, Decimal("7.00"))
        self.assertEqual(self.child2.stockrecords.first().price, Decimal("7.00"))

    def test_submit_increase_by_percentage(self):
        self._seed_session("set_children_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_children": [self.child1.pk, self.child2.pk],
                "increase_by_percentage": "10",
            },
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.stockrecords.first().refresh_from_db()
        self.child2.stockrecords.first().refresh_from_db()
        self.assertEqual(self.child1.stockrecords.first().price, Decimal("5.50"))
        self.assertEqual(self.child2.stockrecords.first().price, Decimal("5.50"))

    def test_submit_multiple_global_options_rerenders_with_error(self):
        self._seed_session("set_children_price")
        page = self.post(
            self._intermediate_url(),
            params={
                "selected_children": [self.child1.pk],
                "new_price": "5.00",
                "increase_by_amount": "1.00",
            },
        )
        self.assertIsOk(page)
        self.assertIn("__all__", page.context["form"].errors)

    def test_submit_negative_base_price_rerenders_with_error(self):
        self._seed_session("set_children_price")
        page = self.post(
            self._intermediate_url(),
            params={"selected_children": [self.child1.pk], "new_price": "-5"},
        )
        self.assertIsOk(page)
        self.assertIn("new_price", page.context["form"].errors)

    def test_submit_no_price_rerenders_with_error(self):
        self._seed_session("set_children_price")
        page = self.post(
            self._intermediate_url(),
            params={"selected_children": [self.child1.pk]},
        )
        self.assertIsOk(page)
        self.assertIn(f"price_{self.child1.pk}", page.context["form"].errors)


class TestIntermediateBulkActionViewSessionGuard(ChildrenBulkActionTests):
    def test_get_without_session_redirects_with_warning(self):
        response = self.get(self._intermediate_url())
        self.assertIsRedirect(response)
        followed = response.follow()
        messages = list(followed.context["messages"])
        self.assertTrue(any("No pending bulk action" in str(m) for m in messages))

    def test_select_all_seeds_all_parents_in_session(self):
        parent2 = create_product(structure="parent")
        parent3 = create_product(structure="parent")
        create_product(structure="child", parent=parent2)
        create_product(structure="child", parent=parent3)

        self.post(
            reverse("dashboard:catalogue-product-list"),
            params={"action": "make_children_public", "select_across": "1"},
        )
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        parents = list(page.context["parents_with_children"])
        self.assertIn(self.parent, parents)
        self.assertIn(parent2, parents)
        self.assertIn(parent3, parents)
