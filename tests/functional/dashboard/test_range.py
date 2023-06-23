import random

from django.contrib.messages.constants import SUCCESS, WARNING
from django.test import TestCase
from django.urls import reverse
from webtest.forms import Upload

from oscar.apps.dashboard.ranges import forms
from oscar.apps.offer.models import Range, RangeProductFileUpload
from oscar.test.factories import create_product
from oscar.test.testcases import WebTestCase


class RangeProductFormTests(TestCase):
    def setUp(self):
        self.range = Range.objects.create(name="dummy")

    def tearDown(self):
        Range.objects.all().delete()

    def submit_form(self, data):
        return forms.RangeProductForm(self.range, data)

    def test_either_query_or_file_must_be_submitted(self):
        form = self.submit_form({"query": ""})
        self.assertFalse(form.is_valid())

    def test_non_match_becomes_error(self):
        form = self.submit_form({"query": "123123"})
        self.assertFalse(form.is_valid())

    def test_matching_query_is_valid(self):
        create_product(partner_sku="123123")
        form = self.submit_form({"query": "123123"})
        self.assertTrue(form.is_valid())

    def test_passing_form_return_product_list(self):
        product = create_product(partner_sku="123123")
        form = self.submit_form({"query": "123123"})
        form.is_valid()
        self.assertEqual(1, len(form.get_products()))
        self.assertEqual(product.id, form.get_products()[0].id)

    def test_missing_skus_are_available(self):
        create_product(partner_sku="123123")
        form = self.submit_form({"query": "123123, 123xxx"})
        form.is_valid()
        self.assertEqual(1, len(form.get_missing_skus()))
        self.assertTrue("123xxx" in form.get_missing_skus())

    def test_only_dupes_is_invalid(self):
        product = create_product(partner_sku="123123")
        self.range.add_product(product)
        form = self.submit_form({"query": "123123"})
        self.assertFalse(form.is_valid())

    def test_dupe_skus_are_available(self):
        product = create_product(partner_sku="123123")
        create_product(partner_sku="123124")
        self.range.add_product(product)
        form = self.submit_form({"query": "123123, 123124"})
        self.assertTrue(form.is_valid())
        self.assertTrue("123123" in form.get_duplicate_skus())


class RangeProductViewTest(WebTestCase):
    is_staff = True

    def setUp(self):
        super().setUp()
        self.range = Range.objects.create(name="dummy")
        self.url = reverse("dashboard:range-products", args=(self.range.id,))
        self.product1 = create_product(
            title="Product 1", partner_sku="123123", partner_name="Partner 1"
        )
        self.product2 = create_product(
            title="Product 2", partner_sku="123123", partner_name="Partner 2"
        )
        self.product3 = create_product(partner_sku="456")
        self.product4 = create_product(partner_sku="789")
        self.parent = create_product(upc="1234", structure="parent")
        self.child1 = create_product(
            upc="1234.345", structure="child", parent=self.parent
        )
        self.child2 = create_product(
            upc="1234-345", structure="child", parent=self.parent
        )

    def test_upload_file_with_skus(self):
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form["file_upload"] = Upload("new_skus.txt", b"456")
        form.submit().follow()
        all_products = self.range.all_products()
        self.assertEqual(len(all_products), 1)
        self.assertTrue(self.product3 in all_products)
        range_product_file_upload = RangeProductFileUpload.objects.get()
        self.assertEqual(range_product_file_upload.range, self.range)
        self.assertEqual(range_product_file_upload.num_new_skus, 1)
        self.assertEqual(
            range_product_file_upload.status, RangeProductFileUpload.PROCESSED
        )
        self.assertEqual(range_product_file_upload.size, 3)

    def test_upload_excluded_file_with_skus(self):
        excluded_products = self.range.excluded_products.all()
        self.assertEqual(len(excluded_products), 0)
        self.assertFalse(self.product3 in excluded_products)

        # Upload the product
        range_products_page = self.get(self.url)
        form = range_products_page.forms[1]
        form["file_upload"] = Upload("new_skus.txt", b"456")
        form.submit().follow()

        excluded_products = self.range.excluded_products.all()
        self.assertEqual(len(excluded_products), 1)
        self.assertTrue(self.product3 in excluded_products)

        range_product_file_upload = RangeProductFileUpload.objects.get()
        self.assertEqual(range_product_file_upload.range, self.range)
        self.assertEqual(range_product_file_upload.num_new_skus, 1)
        self.assertEqual(
            range_product_file_upload.status, RangeProductFileUpload.PROCESSED
        )
        self.assertEqual(range_product_file_upload.size, 3)

    def test_upload_multiple_excluded_file_with_skus(self):
        excluded_products = self.range.excluded_products.all()
        self.assertEqual(len(excluded_products), 0)
        self.assertFalse(self.product3 in excluded_products)
        self.assertFalse(self.product4 in excluded_products)

        # Upload the products
        range_products_page = self.get(self.url)
        form = range_products_page.forms[1]
        form["file_upload"] = Upload("new_skus.txt", b"456,789")
        form.submit().follow()

        excluded_products = self.range.excluded_products.all()
        self.assertEqual(len(excluded_products), 2)
        self.assertTrue(self.product3 in excluded_products)
        self.assertTrue(self.product4 in excluded_products)

        range_product_file_upload = RangeProductFileUpload.objects.get()
        self.assertEqual(range_product_file_upload.range, self.range)
        self.assertEqual(range_product_file_upload.num_new_skus, 2)
        self.assertEqual(
            range_product_file_upload.status, RangeProductFileUpload.PROCESSED
        )
        self.assertEqual(range_product_file_upload.size, 7)

    def test_exclude_skus_textarea_form_field(self):
        excluded_products = self.range.excluded_products.all()
        self.assertEqual(len(excluded_products), 0)
        self.assertFalse(self.product3 in excluded_products)

        range_products_page = self.get(self.url)
        form = range_products_page.forms[1]
        form["query"] = "456"
        form.submit().follow()

        excluded_products = self.range.excluded_products.all()
        self.assertEqual(len(excluded_products), 1)
        self.assertTrue(self.product3 in excluded_products)

    def test_exclude_multiple_skus_textarea_form_field(self):
        excluded_products = self.range.excluded_products.all()
        self.assertEqual(len(excluded_products), 0)
        self.assertFalse(self.product3 in excluded_products)
        self.assertFalse(self.product4 in excluded_products)

        range_products_page = self.get(self.url)
        form = range_products_page.forms[1]
        form["query"] = "456,789"
        form.submit().follow()

        excluded_products = self.range.excluded_products.all()
        self.assertEqual(len(excluded_products), 2)
        self.assertTrue(self.product3 in excluded_products)
        self.assertTrue(self.product4 in excluded_products)

    def test_dupe_skus_warning(self):
        self.range.add_product(self.product3)
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form["query"] = "456"
        response = form.submit()
        self.assertEqual(list(response.context["messages"]), [])
        self.assertEqual(
            response.context["form"].errors["query"],
            [
                "The products with SKUs or UPCs matching 456 have already been added to this range"
            ],
        )

        form = response.forms[0]
        form["query"] = "456, 789"
        response = form.submit().follow()
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, "1 product has been added to this range")
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message,
            "The products with SKUs or UPCs matching 456 have already been added to this range",
        )

    def test_dupe_excluded_skus_warning(self):
        self.range.add_product(self.product3)
        self.range.add_product(self.product4)
        self.range.excluded_products.add(self.product3)
        range_products_page = self.get(self.url)
        form = range_products_page.forms[2]
        form["query"] = "456"
        response = form.submit()
        self.assertEqual(list(response.context["messages"]), [])
        self.assertEqual(
            response.context["form_excluded"].errors["query"],
            [
                "The products with SKUs or UPCs matching 456 have already been excluded from this range"
            ],
        )

        form = response.forms[2]
        form["query"] = "456, 789"
        response = form.submit().follow()
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(
            messages[0].message, "1 product has been excluded from this range"
        )
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message,
            "The products with SKUs or UPCs matching 456 have already been excluded from this range",
        )

    def test_missing_skus_warning(self):
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form["query"] = "321"
        response = form.submit()
        self.assertEqual(list(response.context["messages"]), [])
        self.assertEqual(
            response.context["form"].errors["query"],
            ["No products exist with a SKU or UPC matching 321"],
        )
        form = range_products_page.forms[0]
        form["query"] = "456, 321"
        response = form.submit().follow()
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, "1 product has been added to this range")
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, "No product(s) were found with SKU or UPC matching 321"
        )

    def test_same_skus_within_different_products_warning_query(self):
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form["query"] = "123123"
        response = form.submit().follow()
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, "There are more than one product with SKU 123123"
        )

    def test_same_skus_within_different_products_warning_file_upload(self):
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form["file_upload"] = Upload("skus.txt", b"123123")
        response = form.submit().follow()
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, "There are more than one product with SKU 123123"
        )

    def test_adding_child_does_not_add_parent(self):
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form["query"] = "1234.345"
        form.submit().follow()
        all_products = self.range.all_products()
        self.assertEqual(len(all_products), 1)
        self.assertFalse(self.range.contains_product(self.parent))
        self.assertTrue(self.range.contains_product(self.child1))
        self.assertFalse(self.range.contains_product(self.child2))

        form = range_products_page.forms[0]
        form["query"] = "1234-345"
        form.submit().follow()
        all_products = self.range.all_products()
        self.assertEqual(len(all_products), 1)
        self.assertTrue(self.range.contains_product(self.child1))
        self.assertTrue(self.range.contains_product(self.child2))
        self.assertFalse(self.range.contains_product(self.parent))

    def test_adding_multiple_children_does_not_add_parent(self):
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form["query"] = "1234.345 1234-345"
        form.submit().follow()
        all_products = self.range.all_products()
        self.assertEqual(len(all_products), 2)
        self.assertTrue(self.range.contains_product(self.child1))
        self.assertTrue(self.range.contains_product(self.child2))
        self.assertFalse(self.range.contains_product(self.parent))

    def test_adding_multiple_comma_separated_children_does_not_add_parent(self):
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form["query"] = "1234.345, 1234-345"
        form.submit().follow()
        all_products = self.range.all_products()
        self.assertEqual(len(all_products), 2)
        self.assertTrue(self.range.contains_product(self.child1))
        self.assertTrue(self.range.contains_product(self.child2))
        self.assertFalse(self.range.contains_product(self.parent))

    def test_remove_selected_product(self):
        self.range.add_product(self.product3)
        range_products_page = self.get(self.url)
        form = range_products_page.forms[1]
        form["selected_product"] = "456"
        response = form.submit().follow()
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, "Removed 1 product from range")
        self.assertFalse(self.range.contains_product(self.product3))
        self.assertTrue(self.product3 in self.range.excluded_products.all())

    def test_remove_excluded_product(self):
        self.range.add_product(self.product3)
        self.range.excluded_products.add(self.product3)
        self.assertFalse(self.range.contains_product(self.product3))

        # Remove the product from exclusion form
        range_products_page = self.get(self.url)
        form = range_products_page.forms[2]
        form["selected_product"] = "456"
        response = form.submit().follow()

        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, "Removed 1 product from excluded list")
        self.assertTrue(self.range.contains_product(self.product3))

    def test_remove_multiple_excluded_products(self):
        self.test_upload_multiple_excluded_file_with_skus()
        self.assertIn(self.product3, self.range.excluded_products.all())
        self.assertIn(self.product4, self.range.excluded_products.all())

        range_products_page = self.get(self.url)
        form = range_products_page.forms[2]
        form["selected_product"] = [self.product3.pk, self.product4.pk]
        response = form.submit().follow()

        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, "Removed 2 products from excluded list")
        self.assertNotIn(self.product3, self.range.excluded_products.all())
        self.assertNotIn(self.product4, self.range.excluded_products.all())


class RangeReorderViewTest(WebTestCase):
    is_staff = True
    csrf_checks = False

    def setUp(self):
        super().setUp()
        self.range = Range.objects.create(name="dummy")
        self.url = reverse("dashboard:range-reorder", args=(self.range.id,))
        self.product1 = create_product()
        self.product2 = create_product()
        self.product3 = create_product()
        self.range.included_products.set([self.product1, self.product2, self.product3])

    def test_range_product_reordering(self):
        product_order = list(
            self.range.rangeproduct_set.values_list("product_id", flat=True)
        )
        random.shuffle(product_order)
        data = {"product": product_order}
        self.post(self.url, params=data)
        new_product_order = list(
            self.range.rangeproduct_set.values_list("product_id", flat=True).order_by(
                "display_order"
            )
        )
        self.assertEqual(new_product_order, product_order)
