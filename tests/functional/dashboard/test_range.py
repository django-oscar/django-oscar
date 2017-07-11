from django.contrib.messages.constants import SUCCESS, WARNING
from django.core.urlresolvers import reverse
from django.test import TestCase

from oscar.apps.dashboard.ranges import forms
from oscar.apps.offer.models import Range, RangeProductFileUpload
from oscar.test.factories import create_product
from oscar.test.testcases import WebTestCase

from webtest.forms import Upload


class RangeProductFormTests(TestCase):

    def setUp(self):
        self.range = Range.objects.create(name='dummy')

    def tearDown(self):
        Range.objects.all().delete()

    def submit_form(self, data):
        return forms.RangeProductForm(self.range, data)

    def test_either_query_or_file_must_be_submitted(self):
        form = self.submit_form({'query': ''})
        self.assertFalse(form.is_valid())

    def test_non_match_becomes_error(self):
        form = self.submit_form({'query': '123123'})
        self.assertFalse(form.is_valid())

    def test_matching_query_is_valid(self):
        create_product(partner_sku='123123')
        form = self.submit_form({'query': '123123'})
        self.assertTrue(form.is_valid())

    def test_passing_form_return_product_list(self):
        product = create_product(partner_sku='123123')
        form = self.submit_form({'query': '123123'})
        form.is_valid()
        self.assertEqual(1, len(form.get_products()))
        self.assertEqual(product.id, form.get_products()[0].id)

    def test_missing_skus_are_available(self):
        create_product(partner_sku='123123')
        form = self.submit_form({'query': '123123, 123xxx'})
        form.is_valid()
        self.assertEqual(1, len(form.get_missing_skus()))
        self.assertTrue('123xxx' in form.get_missing_skus())

    def test_only_dupes_is_invalid(self):
        product = create_product(partner_sku='123123')
        self.range.add_product(product)
        form = self.submit_form({'query': '123123'})
        self.assertFalse(form.is_valid())

    def test_dupe_skus_are_available(self):
        product = create_product(partner_sku='123123')
        create_product(partner_sku='123124')
        self.range.add_product(product)
        form = self.submit_form({'query': '123123, 123124'})
        self.assertTrue(form.is_valid())
        self.assertTrue('123123' in form.get_duplicate_skus())


class RangeProductViewTest(WebTestCase):
    is_staff = True

    def setUp(self):
        super(RangeProductViewTest, self).setUp()
        self.range = Range.objects.create(name='dummy')
        self.url = reverse('dashboard:range-products', args=(self.range.id,))
        self.product1 = create_product(
            title='Product 1', partner_sku='123123', partner_name='Partner 1'
        )
        self.product2 = create_product(
            title='Product 2', partner_sku='123123', partner_name='Partner 2'
        )
        self.product3 = create_product(partner_sku='456')
        self.product4 = create_product(partner_sku='789')

    def test_upload_file_with_skus(self):
        range_products_page = self.get(self.url)
        form = range_products_page.form
        form['file_upload'] = Upload('new_skus.txt', b'456')
        form.submit().follow()
        all_products = self.range.all_products()
        self.assertEqual(len(all_products), 1)
        self.assertTrue(self.product3 in all_products)
        range_product_file_upload = RangeProductFileUpload.objects.get()
        self.assertEqual(range_product_file_upload.range, self.range)
        self.assertEqual(range_product_file_upload.num_new_skus, 1)
        self.assertEqual(range_product_file_upload.status, RangeProductFileUpload.PROCESSED)
        self.assertEqual(range_product_file_upload.size, 3)

    def test_dupe_skus_warning(self):
        self.range.add_product(self.product3)
        range_products_page = self.get(self.url)
        form = range_products_page.forms[0]
        form['query'] = '456'
        response = form.submit()
        self.assertEqual(list(response.context['messages']), [])
        self.assertEqual(
            response.context['form'].errors['query'],
            ['The products with SKUs or UPCs matching 456 are already in this range']
        )

        form = response.forms[0]
        form['query'] = '456, 789'
        response = form.submit().follow()
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, '1 product added to range')
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message,
            'The products with SKUs or UPCs matching 456 are already in this range'
        )

    def test_missing_skus_warning(self):
        range_products_page = self.get(self.url)
        form = range_products_page.form
        form['query'] = '321'
        response = form.submit()
        self.assertEqual(list(response.context['messages']), [])
        self.assertEqual(
            response.context['form'].errors['query'],
            ['No products exist with a SKU or UPC matching 321']
        )
        form = range_products_page.form
        form['query'] = '456, 321'
        response = form.submit().follow()
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, '1 product added to range')
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, 'No product(s) were found with SKU or UPC matching 321'
        )

    def test_same_skus_within_different_products_warning_query(self):
        range_products_page = self.get(self.url)
        form = range_products_page.form
        form['query'] = '123123'
        response = form.submit().follow()
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, 'There are more than one product with SKU 123123'
        )

    def test_same_skus_within_different_products_warning_file_upload(self):
        range_products_page = self.get(self.url)
        form = range_products_page.form
        form['file_upload'] = Upload('skus.txt', b'123123')
        response = form.submit().follow()
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, 'There are more than one product with SKU 123123'
        )
