from http import client as http_client
from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    CategoryFactory,
    PartnerFactory,
    ProductAttributeFactory,
    ProductFactory,
    StockRecordFactory,
    create_product,
)
from oscar.test.testcases import WebTestCase, add_permissions

User = get_user_model()
Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductCategory = get_model("catalogue", "ProductCategory")
Category = get_model("catalogue", "Category")
StockRecord = get_model("partner", "stockrecord")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")

AttributeOptionGroupForm = get_class(
    "dashboard.catalogue.forms", "AttributeOptionGroupForm"
)
AttributeOptionFormSet = get_class(
    "dashboard.catalogue.formsets", "AttributeOptionFormSet"
)
RelatedFieldWidgetWrapper = get_class("dashboard.widgets", "RelatedFieldWidgetWrapper")
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class TestCatalogueViews(WebTestCase):
    is_staff = True
    csrf_checks = False
    permissions = DashboardPermission.get(
        "catalogue", "view_product", "change_product", "view_category"
    ) + DashboardPermission.get("partner", "view_stockalert")

    def test_exist(self):
        urls = [
            reverse("dashboard:catalogue-product-list"),
            reverse("dashboard:catalogue-category-list"),
            reverse("dashboard:stock-alert-list"),
            reverse("dashboard:catalogue-product-lookup"),
            reverse("dashboard:catalogue-partner-lookup"),
        ]
        for url in urls:
            self.assertIsOk(self.get(url))

    def test_partner_lookup_filters_by_name(self):
        partner = PartnerFactory(name="Findable partner")
        PartnerFactory(name="Someone else")
        response = self.get(
            reverse("dashboard:catalogue-partner-lookup"), params={"q": "Findable"}
        )
        ids = [result["id"] for result in response.json["results"]]
        self.assertEqual(ids, [partner.id])

    def test_upc_filter(self):
        product1 = create_product(upc="123")
        product2 = create_product(upc="12")
        product3 = create_product(upc="1")

        # no value for upc, all results
        page = self.get("%s?upc=" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertIn(product3, products_on_page)

        # filter by upc, one result
        page = self.get("%s?upc=123" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # exact match, one result, no multiple
        page = self.get("%s?upc=12" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertNotIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # part of the upc, one result
        page = self.get("%s?upc=3" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # part of the upc, two results
        page = self.get("%s?upc=2" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

    def test_is_public(self):
        # Can I still find non-public products in dashboard?
        product = create_product(is_public=False, upc="kleine-bats")
        page = self.get(
            "%s?upc=%s" % (reverse("dashboard:catalogue-product-list"), product.upc)
        )
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertEqual(products_on_page, [product])

    def _intermediate_url_with_token(self, seed_response):
        location = getattr(seed_response, "location", "") or ""
        token = parse_qs(urlparse(location).query).get("key", [None])[0]
        url = reverse("dashboard:catalogue-product-bulk-action")
        return "%s?key=%s" % (url, token) if token else url

    def test_make_public(self):
        a = create_product(upc="A", is_public=False)
        seed_response = self.post(
            reverse("dashboard:catalogue-product-list"),
            params={"action": "make_products_public", "selected_product": [a.id]},
        )
        response = self.post(
            self._intermediate_url_with_token(seed_response),
            params={"selected_products": [a.id]},
        )
        self.assertIsRedirect(response)
        a.refresh_from_db()
        self.assertTrue(a.is_public)

    def test_make_non_public(self):
        b = create_product(upc="B")
        seed_response = self.post(
            reverse("dashboard:catalogue-product-list"),
            params={"action": "make_products_non_public", "selected_product": [b.id]},
        )
        response = self.post(
            self._intermediate_url_with_token(seed_response),
            params={"selected_products": [b.id]},
        )
        self.assertIsRedirect(response)
        b.refresh_from_db()
        self.assertFalse(b.is_public)


class TestAStaffUser(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get(
        "catalogue", "view_product", "change_product", "delete_product", "add_product"
    )

    def setUp(self):
        super().setUp()
        self.partner = PartnerFactory()

    def test_can_create_a_product_without_stockrecord(self):
        category = CategoryFactory()
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(
            reverse("dashboard:catalogue-product-create", args=(product_class.slug,))
        )
        form = page.forms["create_update_product_form"]
        form["upc"] = "123456"
        form["title"] = "new product"
        form["productcategory_set-0-category"] = category.id
        form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_create_and_continue_editing_a_product(self):
        category = CategoryFactory()
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(
            reverse("dashboard:catalogue-product-create", args=(product_class.slug,))
        )
        form = page.forms["create_update_product_form"]
        form["upc"] = "123456"
        form["title"] = "new product"
        form["productcategory_set-0-category"] = category.id
        # The partner field is a remote select (see #4565); the choices are
        # loaded with AJAX, so WebTest can't find the option in the markup.
        form["stockrecords-0-partner"].force_value(self.partner.id)
        form["stockrecords-0-partner_sku"] = "14"
        form["stockrecords-0-num_in_stock"] = "555"
        form["stockrecords-0-price"] = "13.99"
        page = form.submit(name="action", value="continue")

        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.all()[0]
        self.assertEqual(product.stockrecords.all()[0].partner, self.partner)
        self.assertRedirects(
            page, reverse("dashboard:catalogue-product", kwargs={"pk": product.id})
        )

    def test_can_change_the_partner_of_a_stockrecord(self):
        old_partner = PartnerFactory(users=[self.user])
        new_partner = PartnerFactory(users=[self.user])
        product = ProductFactory(stockrecords=[])
        StockRecordFactory(product=product, partner=old_partner)
        url = reverse("dashboard:catalogue-product", kwargs={"pk": product.id})
        form = self.get(url).forms["create_update_product_form"]
        form["stockrecords-0-partner"].force_value(new_partner.id)
        form.submit()

        self.assertEqual(product.stockrecords.get().partner, new_partner)

    def test_can_update_a_product_without_stockrecord(self):
        new_title = "foobar"
        category = CategoryFactory()
        product = ProductFactory(stockrecords=[])

        page = self.get(
            reverse("dashboard:catalogue-product", kwargs={"pk": product.id})
        )
        form = page.forms["create_update_product_form"]
        form["productcategory_set-0-category"] = category.id
        self.assertNotEqual(form["title"].value, new_title)
        form["title"] = new_title
        form.submit()

        try:
            product = Product.objects.get(pk=product.pk)
        except Product.DoesNotExist:
            pass
        else:
            self.assertTrue(product.title == new_title)
            if product.has_stockrecords:
                self.fail("Product has stock records but should not")

    def test_can_create_product_with_required_attributes(self):
        category = CategoryFactory()
        attribute = ProductAttributeFactory(required=True)
        product_class = attribute.product_class
        page = self.get(
            reverse("dashboard:catalogue-product-create", args=(product_class.slug,))
        )
        form = page.forms["create_update_product_form"]
        form["upc"] = "123456"
        form["title"] = "new product"
        form["attr_weight"] = "5"
        form["productcategory_set-0-category"] = category.id
        form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_delete_a_standalone_product(self):
        product = create_product(partner_users=[self.user])
        category = Category.add_root(name="Test Category")
        ProductCategory.objects.create(category=category, product=product)

        page = (
            self.get(reverse("dashboard:catalogue-product-delete", args=(product.id,)))
            .forms["delete_product_form"]
            .submit()
        )

        self.assertRedirects(page, reverse("dashboard:catalogue-product-list"))
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(StockRecord.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(ProductCategory.objects.count(), 0)

    def test_can_delete_a_parent_product(self):
        parent_product = create_product(structure="parent")
        create_product(parent=parent_product)

        url = reverse("dashboard:catalogue-product-delete", args=(parent_product.id,))
        page = self.get(url).forms["delete_product_form"].submit()

        self.assertRedirects(page, reverse("dashboard:catalogue-product-list"))
        self.assertEqual(Product.objects.count(), 0)

    def test_can_delete_a_child_product(self):
        parent_product = create_product(structure="parent")
        child_product = create_product(parent=parent_product)

        url = reverse("dashboard:catalogue-product-delete", args=(child_product.id,))
        page = self.get(url).forms["delete_product_form"].submit()

        expected_url = reverse(
            "dashboard:catalogue-product", kwargs={"pk": parent_product.pk}
        )
        self.assertRedirects(page, expected_url)
        self.assertEqual(Product.objects.count(), 1)

        # if last child is deleted, it must turn parent product into a stand-alone product
        parent_product.refresh_from_db()
        self.assertEqual(parent_product.structure, "standalone")

    def test_can_list_her_products(self):
        product1 = create_product(
            partner_users=[
                self.user,
            ]
        )
        product2 = create_product(partner_name="sneaky", partner_users=[])
        page = self.get(reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)

    def test_can_create_a_child_product(self):
        parent_product = create_product(structure="parent")
        url = reverse(
            "dashboard:catalogue-product-create-child",
            kwargs={"parent_pk": parent_product.pk},
        )
        form = self.get(url).forms["create_update_product_form"]
        form.submit()

        self.assertEqual(Product.objects.count(), 2)

    def test_cant_create_child_product_for_invalid_parents(self):
        # Creates a product with stockrecords.
        invalid_parent = create_product(partner_users=[self.user])
        self.assertFalse(invalid_parent.can_be_parent())
        url = reverse(
            "dashboard:catalogue-product-create-child",
            kwargs={"parent_pk": invalid_parent.pk},
        )
        self.assertRedirects(self.get(url), reverse("dashboard:catalogue-product-list"))


class TestANonStaffUser(TestAStaffUser):
    is_staff = False
    is_anonymous = False
    permissions = DashboardPermission.partner_dashboard_access

    def setUp(self):
        super().setUp()
        add_permissions(self.user, self.permissions)
        self.partner.users.add(self.user)

    def test_can_list_her_products(self):
        product1 = create_product(partner_name="A", partner_users=[self.user])
        product2 = create_product(partner_name="B", partner_users=[])
        page = self.get(reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)

    def test_cant_create_a_child_product(self):
        parent_product = create_product(structure="parent")
        url = reverse(
            "dashboard:catalogue-product-create-child",
            kwargs={"parent_pk": parent_product.pk},
        )
        response = self.get(url, status="*")
        self.assertEqual(http_client.FORBIDDEN, response.status_code)

    def test_partner_lookup_only_returns_her_partners(self):
        other_partner = PartnerFactory(name="Someone else")
        response = self.get(reverse("dashboard:catalogue-partner-lookup"))
        ids = [result["id"] for result in response.json["results"]]
        self.assertIn(self.partner.id, ids)
        self.assertNotIn(other_partner.id, ids)

    # Tests below can't work because they don't create a stockrecord

    def test_can_create_a_product_without_stockrecord(self):
        pass

    def test_can_update_a_product_without_stockrecord(self):
        pass

    def test_can_create_product_with_required_attributes(self):
        pass

    # Tests below can't work because child products aren't supported with the
    # permission-based dashboard

    def test_can_delete_a_child_product(self):
        pass

    def test_can_delete_a_parent_product(self):
        pass

    def test_can_create_a_child_product(self):
        pass

    def test_cant_create_child_product_for_invalid_parents(self):
        pass


class TestProductUpdatePageWeight(WebTestCase):
    """Regression test for #4565.

    The partner field rendered every partner as an <option> in every
    stockrecord row, so the page grew with partners * stockrecords.
    """

    is_staff = True
    permissions = DashboardPermission.get(
        "catalogue", "view_product", "change_product", "add_product"
    )

    def test_page_weight_does_not_scale_with_partner_count(self):
        partners = PartnerFactory.create_batch(4)
        product = ProductFactory(stockrecords=[])
        for partner in partners:
            StockRecordFactory(product=product, partner=partner)
        url = reverse("dashboard:catalogue-product", kwargs={"pk": product.id})

        before = len(self.get(url).body)
        # Adding 100 partners used to add a full <option> to each of the five
        # stockrecord selects on this page: about 200 bytes per partner.
        PartnerFactory.create_batch(100)
        after = len(self.get(url).body)

        self.assertLess((after - before) / 100, 10)


class TestProductCreatePageWithUnicodeSlug(TestCase):
    def setUp(self):
        self.slug = "Ûul-wįth-weird-chars"
        ProductClass.objects.create(name="Book", slug=self.slug)
        self.user = User.objects.create(is_staff=True)
        add_permissions(
            self.user,
            DashboardPermission.get("catalogue", "view_product", "add_product"),
        )
        self.client.force_login(self.user)

    def test_url_with_unicode_characters(self):
        response = self.client.get(f"/dashboard/catalogue/products/create/{self.slug}/")
        self.assertEqual(200, response.status_code)
