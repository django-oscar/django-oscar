import time
from decimal import Decimal
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlparse

from django.urls import reverse

from oscar.core.loading import get_class, get_model
from oscar.test.factories import create_product, create_stockrecord
from oscar.test.testcases import WebTestCase

Product = get_model("catalogue", "Product")

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class ProductBulkActionTests(WebTestCase):
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
        # Both stockrecords share the same (default) partner.
        self.partner = self.child1.stockrecords.first().partner
        self._token = None

    def _token_from_redirect(self, response):
        location = getattr(response, "location", "") or ""
        return parse_qs(urlparse(location).query).get("key", [None])[0]

    def _seed_session(self, action):
        response = self.post(
            reverse("dashboard:catalogue-product-list"),
            params={"action": action, "selected_product": [self.parent.pk]},
        )
        self._token = self._token_from_redirect(response)
        return response

    def _intermediate_url(self):
        url = reverse("dashboard:catalogue-product-bulk-action")
        token = getattr(self, "_token", None)
        return "%s?key=%s" % (url, token) if token else url


class TestMakeProductsPublicFlow(ProductBulkActionTests):
    def test_list_post_redirects_to_intermediate(self):
        response = self._seed_session("make_products_public")
        # assertIsRedirect only compares the path, not the ?key= token.
        self.assertIsRedirect(
            response, reverse("dashboard:catalogue-product-bulk-action")
        )

    def test_get_intermediate_view_renders_form(self):
        self._seed_session("make_products_public")
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        self.assertInContext(page, "form")
        parents = [
            row["product"]
            for row in page.context["display_rows"]
            if row["is_group_header"]
        ]
        self.assertIn(self.parent, parents)

    def test_submit_makes_children_public(self):
        self._seed_session("make_products_public")
        response = self.post(
            self._intermediate_url(),
            params={"selected_products": [self.child1.pk, self.child2.pk]},
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertTrue(self.child1.is_public)
        self.assertTrue(self.child2.is_public)

    def test_session_cleared_after_submit(self):
        self._seed_session("make_products_public")
        self.post(
            self._intermediate_url(),
            params={"selected_products": [self.child1.pk]},
        )
        response = self.get(self._intermediate_url())
        self.assertIsRedirect(response)


class TestMakeProductsNonPublicFlow(ProductBulkActionTests):
    def setUp(self):
        super().setUp()
        self.child1.is_public = True
        self.child1.save()
        self.child2.is_public = True
        self.child2.save()

    def test_submit_makes_children_non_public(self):
        self._seed_session("make_products_non_public")
        response = self.post(
            self._intermediate_url(),
            params={"selected_products": [self.child1.pk, self.child2.pk]},
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertFalse(self.child1.is_public)
        self.assertFalse(self.child2.is_public)

    def test_empty_selection_rerenders_with_error(self):
        self._seed_session("make_products_non_public")
        page = self.post(self._intermediate_url(), params={})
        self.assertIsOk(page)
        form = page.context["form"]
        self.assertIn("selected_products", form.errors)
        self.assertIn("Select at least one product.", form.errors["selected_products"])


class TestSetProductPriceFlow(ProductBulkActionTests):
    def test_list_post_redirects_to_intermediate(self):
        response = self._seed_session("set_product_price")
        # assertIsRedirect only compares the path, not the ?key= token.
        self.assertIsRedirect(
            response, reverse("dashboard:catalogue-product-bulk-action")
        )

    def test_get_shows_price_form(self):
        self._seed_session("set_product_price")
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        form = page.context["form"]
        self.assertIn("new_price", form.fields)

    def test_submit_valid_base_price(self):
        self._seed_session("set_product_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk, self.child2.pk],
                "partners": [self.partner.pk],
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
        self._seed_session("set_product_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk, self.child2.pk],
                "partners": [self.partner.pk],
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
        self._seed_session("set_product_price")
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        form = page.context["form"]
        child_pks = [c.pk for c in form.fields["selected_products"].queryset]
        self.assertIn(self.child1.pk, child_pks)
        self.assertIn(self.child2.pk, child_pks)
        self.assertNotIn(child_no_sr.pk, child_pks)

    def test_submit_increase_by_amount(self):
        self._seed_session("set_product_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk, self.child2.pk],
                "partners": [self.partner.pk],
                "increase_by_amount": "2.00",
            },
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.stockrecords.first().refresh_from_db()
        self.child2.stockrecords.first().refresh_from_db()
        self.assertEqual(self.child1.stockrecords.first().price, Decimal("7.00"))
        self.assertEqual(self.child2.stockrecords.first().price, Decimal("7.00"))

    def test_submit_increase_by_percentage(self):
        self._seed_session("set_product_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk, self.child2.pk],
                "partners": [self.partner.pk],
                "increase_by_percentage": "10",
            },
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.stockrecords.first().refresh_from_db()
        self.child2.stockrecords.first().refresh_from_db()
        self.assertEqual(self.child1.stockrecords.first().price, Decimal("5.50"))
        self.assertEqual(self.child2.stockrecords.first().price, Decimal("5.50"))

    def test_submit_multiple_global_options_rerenders_with_error(self):
        self._seed_session("set_product_price")
        page = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "new_price": "5.00",
                "increase_by_amount": "1.00",
            },
        )
        self.assertIsOk(page)
        self.assertIn("__all__", page.context["form"].errors)

    def test_submit_negative_base_price_rerenders_with_error(self):
        self._seed_session("set_product_price")
        page = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
                "new_price": "-5",
            },
        )
        self.assertIsOk(page)
        self.assertIn("new_price", page.context["form"].errors)

    def test_submit_no_price_rerenders_with_error(self):
        self._seed_session("set_product_price")
        page = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk],
                "partners": [self.partner.pk],
            },
        )
        self.assertIsOk(page)
        self.assertIn("__all__", page.context["form"].errors)

    def test_submit_without_partners_rerenders_with_error(self):
        self._seed_session("set_product_price")
        page = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk],
                "new_price": "19.99",
            },
        )
        self.assertIsOk(page)
        self.assertIn("partners", page.context["form"].errors)

    def test_submit_partial_overrides_only_updates_products_with_price(self):
        self._seed_session("set_product_price")
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child1.pk, self.child2.pk],
                "partners": [self.partner.pk],
                f"price_{self.child1.pk}": "11.00",
                # child2 has no override and no global — should be skipped
            },
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.child1.stockrecords.first().refresh_from_db()
        self.child2.stockrecords.first().refresh_from_db()
        self.assertEqual(self.child1.stockrecords.first().price, Decimal("11.00"))
        self.assertEqual(self.child2.stockrecords.first().price, Decimal("5.00"))


class TestIntermediateBulkActionViewSessionGuard(ProductBulkActionTests):
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

        response = self.post(
            reverse("dashboard:catalogue-product-list"),
            params={"action": "make_products_public", "select_across": "1"},
        )
        self._token = self._token_from_redirect(response)
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        parents = [
            row["product"]
            for row in page.context["display_rows"]
            if row["is_group_header"]
        ]
        self.assertIn(self.parent, parents)
        self.assertIn(parent2, parents)
        self.assertIn(parent3, parents)

    def test_concurrent_actions_use_separate_tokens(self):
        token1 = self._token_from_redirect(self._seed_session("make_products_public"))
        token2 = self._token_from_redirect(
            self._seed_session("make_products_non_public")
        )
        self.assertIsNotNone(token1)
        self.assertNotEqual(token1, token2)
        # Both buckets resolve independently; the second seed didn't clobber the first.
        self._token = token1
        self.assertIsOk(self.get(self._intermediate_url()))
        self._token = token2
        self.assertIsOk(self.get(self._intermediate_url()))

    def test_submitting_one_action_leaves_other_bucket_intact(self):
        token1 = self._token_from_redirect(self._seed_session("make_products_public"))
        token2 = self._token_from_redirect(
            self._seed_session("make_products_non_public")
        )
        # Complete the first action.
        self._token = token1
        self.post(
            self._intermediate_url(),
            params={"selected_products": [self.child1.pk]},
        )
        # The other tab's pending action is still usable.
        self._token = token2
        self.assertIsOk(self.get(self._intermediate_url()))


class TestSelectAllByType(ProductBulkActionTests):
    """
    The toolbar provides per-type "select all" checkboxes that include products
    beyond the display limit. Structure counts are always the full selectable set.
    """

    display_limit_path = "oscar.apps.dashboard.catalogue.views.ProductBulkActionConfirmView.max_displayable_products"

    def test_get_shows_per_type_counts_in_context(self):
        self._seed_session("make_products_public")
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        self.assertEqual(page.context["child_count"], 2)
        self.assertEqual(page.context["standalone_count"], 0)
        self.assertEqual(page.context["parent_count"], 1)

    def test_get_shows_hidden_count_when_display_limit_exceeded(self):
        self._seed_session("make_products_public")
        with patch(self.display_limit_path, new=1):
            page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        self.assertGreater(page.context["hidden_count"], 0)

    def test_post_select_all_children_updates_all_children(self):
        self._seed_session("make_products_public")
        response = self.post(
            self._intermediate_url(),
            params={"select_all_children": "on"},
        )
        self.assertIsRedirect(response)
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertTrue(self.child1.is_public)
        self.assertTrue(self.child2.is_public)

    def test_post_select_all_children_includes_products_beyond_display_limit(self):
        self._seed_session("make_products_public")
        with patch(self.display_limit_path, new=1):
            response = self.post(
                self._intermediate_url(),
                params={"select_all_children": "on"},
            )
        self.assertIsRedirect(response)
        self.child1.refresh_from_db()
        self.child2.refresh_from_db()
        self.assertTrue(self.child1.is_public)
        self.assertTrue(self.child2.is_public)


class TestSetProductPriceFlowPartnerIsolation(WebTestCase):
    """
    Full-stack check that a non-staff partner user can never see or edit
    another partner's variants/stockrecords through the bulk price flow.
    """

    is_staff = False
    csrf_checks = False
    permissions = DashboardPermission.partner_dashboard_access

    def setUp(self):
        super().setUp()
        self.parent = create_product(structure="parent")
        self.child_own = create_product(structure="child", parent=self.parent)
        self.child_foreign = create_product(structure="child", parent=self.parent)

        self.sr_own = create_stockrecord(
            self.child_own,
            price=Decimal("5.00"),
            partner_name="Own Partner",
            partner_users=[self.user],
        )
        self.sr_foreign = create_stockrecord(
            self.child_foreign, price=Decimal("5.00"), partner_name="Foreign Partner"
        )
        self.partner_own = self.sr_own.partner
        self._token = None

    def _token_from_redirect(self, response):
        location = getattr(response, "location", "") or ""
        return parse_qs(urlparse(location).query).get("key", [None])[0]

    def _intermediate_url(self):
        url = reverse("dashboard:catalogue-product-bulk-action")
        token = getattr(self, "_token", None)
        return "%s?key=%s" % (url, token) if token else url

    def _seed_session(self):
        response = self.post(
            reverse("dashboard:catalogue-product-list"),
            params={
                "action": "set_product_price",
                "selected_product": [self.parent.pk],
            },
        )
        self._token = self._token_from_redirect(response)
        return response

    def test_foreign_partner_variant_not_in_selectable_products(self):
        self._seed_session()
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        selectable_pks = {
            p.pk for p in page.context["form"].fields["selected_products"].queryset
        }
        self.assertIn(self.child_own.pk, selectable_pks)
        self.assertNotIn(self.child_foreign.pk, selectable_pks)

    def test_foreign_partner_variant_not_in_display_rows(self):
        self._seed_session()
        page = self.get(self._intermediate_url())
        displayed_pks = {row["product"].pk for row in page.context["display_rows"]}
        self.assertIn(self.child_own.pk, displayed_pks)
        self.assertNotIn(self.child_foreign.pk, displayed_pks)

    def test_partners_field_hidden_for_single_partner(self):
        self._seed_session()
        page = self.get(self._intermediate_url())
        field = page.context["form"].fields["partners"]
        self.assertTrue(field.widget.is_hidden)

    def test_submit_only_updates_own_partners_stockrecord(self):
        self._seed_session()
        response = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child_own.pk],
                "partners": [self.partner_own.pk],
                "new_price": "20.00",
            },
        )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        self.sr_own.refresh_from_db()
        self.sr_foreign.refresh_from_db()
        self.assertEqual(self.sr_own.price, Decimal("20.00"))
        self.assertEqual(self.sr_foreign.price, Decimal("5.00"))

    def test_forcing_foreign_product_into_selection_is_rejected(self):
        self._seed_session()
        page = self.post(
            self._intermediate_url(),
            params={
                "selected_products": [self.child_foreign.pk],
                "partners": [self.partner_own.pk],
                "new_price": "20.00",
            },
        )
        self.assertIsOk(page)
        self.assertIn("selected_products", page.context["form"].errors)
        self.sr_foreign.refresh_from_db()
        self.assertEqual(self.sr_foreign.price, Decimal("5.00"))

    def test_cheapest_price_never_shows_a_foreign_partners_lower_price(self):
        # child_own already has sr_own at 5.00 under "Own Partner". Give it
        # an even cheaper stockrecord under a foreign partner too.
        create_stockrecord(
            self.child_own, price=Decimal("1.00"), partner_name="Foreign Partner"
        )
        self._seed_session()
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        products_by_pk = {
            row["product"].pk: row["product"] for row in page.context["display_rows"]
        }
        self.assertEqual(
            products_by_pk[self.child_own.pk].cheapest_price, Decimal("5.00")
        )


class TestQuerySelection(ProductBulkActionTests):
    """
    "Select all" stores the list's query instead of the product ids, so a
    selection can hold any number of products.
    """

    list_view_path = "oscar.apps.dashboard.catalogue.views.ProductListView"
    display_limit_path = "oscar.apps.dashboard.catalogue.views.ProductBulkActionConfirmView.max_displayable_products"

    def _select_all(self, action="make_products_public", query=""):
        url = reverse("dashboard:catalogue-product-list") + query
        response = self.post(url, params={"action": action, "select_across": "1"})
        self._token = self._token_from_redirect(response)
        return response

    def _session_bucket(self):
        return self.app.session["bulk_intermediate"][self._token]

    def _messages(self, page):
        return [str(message) for message in page.context["messages"]]

    def test_select_all(self):
        standalones = [create_product(is_public=False) for _ in range(3)]
        self._select_all()
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        self.assertEqual(page.context["selection_count"], 4)

        self.post(
            self._intermediate_url(),
            params={"select_all_standalones": "on", "select_all_children": "on"},
        )
        for product in standalones + [self.child1, self.child2]:
            product.refresh_from_db()
            self.assertTrue(product.is_public)

    def test_selection_follows_the_list_search(self):
        other = create_product(title="Something else")
        self._select_all(query="?" + urlencode({"title": self.parent.title}))
        page = self.get(self._intermediate_url())
        self.assertEqual(page.context["selection_count"], 1)
        self.assertEqual(page.context["parent_count"], 1)
        self.assertEqual(page.context["standalone_count"], 0)
        self.assertNotIn(
            other, [row["product"] for row in page.context["display_rows"]]
        )

    def test_ticked_products_are_stored_as_ids(self):
        self._seed_session("make_products_public")
        bucket = self._session_bucket()
        self.assertEqual(bucket["ids"], [self.parent.pk])

    def test_a_full_page_can_be_ticked(self):
        # ticked products are not capped; they are at most one page of the list
        others = [create_product() for _ in range(3)]
        ticked = [self.parent.pk] + [product.pk for product in others]
        response = self.post(
            reverse("dashboard:catalogue-product-list"),
            params={"action": "make_products_public", "selected_product": ticked},
        )
        self._token = self._token_from_redirect(response)
        self.assertEqual(sorted(self._session_bucket()["ids"]), sorted(ticked))
        page = self.get(self._intermediate_url())
        self.assertEqual(page.context["selection_count"], 4)

    def test_max_bulk_selection(self):
        create_product()
        with patch("%s.max_bulk_selection" % self.list_view_path, new=1):
            response = self._select_all()
        page = response.follow()
        self.assertTrue(any("Too many" in m for m in self._messages(page)))
        self.assertIsNone(self._token)

    def test_small_selection_is_listed(self):
        self._select_all(action="set_product_price")
        page = self.get(self._intermediate_url())
        self.assertTrue(page.context["can_display_products"])
        self.assertTrue(page.context["display_rows"])
        self.assertNotContains(page, 'id="bulk-price-not-listed"')
        self.assertNotContains(page, 'id="bulk-list-limit-hint"')

    def test_large_selection_is_selected_by_type(self):
        self._select_all(action="set_product_price")
        with patch(self.display_limit_path, new=1):
            page = self.get(self._intermediate_url())
        self.assertFalse(page.context["can_display_products"])
        self.assertEqual(page.context["display_rows"], [])
        self.assertContains(page, "too many to list")
        self.assertContains(page, "listed one by one up to 1 products")
        self.assertContains(
            page, "<code>OSCAR_PRODUCT_BULK_ACTION_MAX_DISPLAYABLE_PRODUCTS</code>"
        )
        # the price action explains why there are no specific prices
        self.assertContains(page, 'id="bulk-price-not-listed"')
        self.assertContains(page, "when there are 1 or fewer")
        # no specific price fields for products that aren't listed
        self.assertFalse(
            [name for name in page.context["form"].fields if name.startswith("price_")]
        )

    def test_large_selection_price(self):
        self._select_all(action="set_product_price")
        with patch(self.display_limit_path, new=1):
            response = self.post(
                self._intermediate_url(),
                params={
                    "select_all_children": "on",
                    "partners": [self.partner.pk],
                    "new_price": "7.50",
                },
            )
        self.assertRedirectsTo(response, "dashboard:catalogue-product-list")
        for child in (self.child1, self.child2):
            self.assertEqual(
                child.stockrecords.get().price, Decimal("7.50"), child.title
            )

    def test_changed_selection_is_shown(self):
        self._select_all()
        create_product()
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        self.assertTrue(any("selection changed" in m for m in self._messages(page)))
        self.assertEqual(page.context["selection_count"], 2)
        self.assertEqual(self._session_bucket()["count"], 2)

        # the next page compares with what was shown
        page = self.get(self._intermediate_url())
        self.assertFalse(any("selection changed" in m for m in self._messages(page)))

    def test_changed_selection_is_not_executed(self):
        self._select_all()
        self.get(self._intermediate_url())
        added = create_product(is_public=False)

        response = self.post(
            self._intermediate_url(), params={"select_all_standalones": "on"}
        )
        self.assertEqual(
            response.location, self._intermediate_url().replace("http://testserver", "")
        )
        added.refresh_from_db()
        self.assertFalse(added.is_public)
        page = response.follow()
        self.assertTrue(any("selection changed" in m for m in self._messages(page)))

        # submitting again executes on the selection that was shown
        self.post(self._intermediate_url(), params={"select_all_standalones": "on"})
        added.refresh_from_db()
        self.assertTrue(added.is_public)

    def test_selection_stored_as_ids_before_new_query_based_change(self):
        self._seed_session("make_products_public")
        session = self.app.session
        session["bulk_intermediate"][self._token] = {
            "action": "make_products_public",
            "created_at": time.time(),
            "object_ids": [self.parent.pk],
        }
        session.save()

        # without a path, the selection was made on the list at the cancel url
        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        self.assertEqual(page.context["selection_count"], 1)
        self.assertEqual(page.context["child_count"], 2)

    def test_ticked_selection_change_with_same_count_is_caught(self):
        # a ticked selection stores the exact ids last shown, so a change that
        # keeps the count the same -- one product drops out as another
        # reappears -- is still noticed. The count alone would not reveal it.
        other = create_product()
        self._seed_session("make_products_public")
        session = self.app.session
        bucket = session["bulk_intermediate"][self._token]
        self.assertEqual(bucket["count"], 1)
        # the page last showed a different product, though just as many
        bucket["fingerprint"] = [other.pk]
        session["bulk_intermediate"][self._token] = bucket
        session.save()

        page = self.get(self._intermediate_url())
        self.assertIsOk(page)
        self.assertEqual(page.context["selection_count"], 1)
        self.assertTrue(any("selection changed" in m for m in self._messages(page)))

        # once shown, the next visit is quiet
        page = self.get(self._intermediate_url())
        self.assertFalse(any("selection changed" in m for m in self._messages(page)))


class TestQuerySelectionPartnerIsolation(TestSetProductPriceFlowPartnerIsolation):
    def test_select_all_holds_only_own_products(self):
        foreign = create_product()
        create_stockrecord(foreign, partner_name="Foreign Partner")
        response = self.post(
            reverse("dashboard:catalogue-product-list"),
            params={"action": "set_product_price", "select_across": "1"},
        )
        self._token = self._token_from_redirect(response)
        page = self.get(self._intermediate_url())
        self.assertEqual(page.context["selection_count"], 1)
        self.assertEqual(page.context["standalone_count"], 0)
        self.assertEqual(page.context["child_count"], 1)
