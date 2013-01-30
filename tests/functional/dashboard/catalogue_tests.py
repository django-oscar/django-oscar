from django.db.models import get_model
from django.core.urlresolvers import reverse

from oscar_testsupport.testcases import ClientTestCase
from oscar_testsupport.factories import create_product

from django_dynamic_fixture import G
from oscar_testsupport.testcases import WebTestCase

User = get_model('auth', 'User')
Product = get_model('catalogue', 'Product')
ProductCategory = get_model('catalogue', 'ProductCategory')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'stockrecord')


class TestCatalogueViews(ClientTestCase):
    is_staff = True

    def test_exist(self):
        urls = [reverse('dashboard:catalogue-product-list'),
                reverse('dashboard:catalogue-category-list'),
                reverse('dashboard:stock-alert-list'),
               ]
        for url in urls:
            self.assertIsOk(self.client.get(url))


class TestAStaffUser(WebTestCase):
    is_staff = True

    def test_can_submit_an_invalid_product_update_and_returns_to_update_page(self):
        product = G(Product, ignore_fields=['stockrecord'], parent=None)

        form = self.get(
            reverse('dashboard:catalogue-product',
                    kwargs={'pk': product.id})
        ).forms[0]
        assert form['partner'].value == u''

        page = form.submit()
        self.assertFalse(page.context['stockrecord_form'].is_valid())

    def test_can_update_a_product_without_stockrecord(self):
        category = G(Category)
        product = G(Product, ignore_fields=['stockrecord'], parent=None)

        page = self.get(
            reverse('dashboard:catalogue-product',
                    kwargs={'pk': product.id})
        )
        form = page.forms[0]
        form['productcategory_set-0-category'] = category.id
        assert form['partner'].value == u''

        form.submit()

        try:
            product = Product.objects.get(pk=product.pk)
        except Product.DoesNotExist:
            pass
        else:
            if product.has_stockrecord:
                self.fail('product has stock record but should not')

    def test_can_delete_an_individual_product(self):
        product = create_product()
        stockrecord = product.stockrecord

        category = Category.add_root(name='Test Category')
        product_category = ProductCategory.objects.create(category=category,
                                                          product=product)

        page = self.get(reverse('dashboard:catalogue-product-delete',
                                args=(product.id,))).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-product-list'))

        self.assertEquals(Product.objects.count(), 0)
        self.assertEquals(StockRecord.objects.count(), 0)
        self.assertEquals(ProductCategory.objects.count(), 0)

        self.assertRaises(Product.DoesNotExist,
                          Product.objects.get, id=product.id)
        self.assertRaises(StockRecord.DoesNotExist,
                          StockRecord.objects.get, id=stockrecord.id)
        self.assertRaises(ProductCategory.DoesNotExist,
                          ProductCategory.objects.get, id=product_category.id)

    def test_can_delete_a_canonical_product(self):
        canonical_product = create_product(title="Canonical Product")

        product = create_product(title="Variant 1", parent=canonical_product)
        stockrecord = product.stockrecord

        category = Category.add_root(name='Test Category')
        product_category = ProductCategory.objects.create(category=category,
                                                          product=product)

        page = self.get(reverse('dashboard:catalogue-product-delete',
                                args=(canonical_product.id,))).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-product-list'))

        self.assertEquals(Product.objects.count(), 0)
        self.assertEquals(StockRecord.objects.count(), 0)
        self.assertEquals(ProductCategory.objects.count(), 0)

        self.assertRaises(Product.DoesNotExist,
                          Product.objects.get, id=canonical_product.id)

        self.assertRaises(Product.DoesNotExist,
                          Product.objects.get, id=product.id)
        self.assertRaises(StockRecord.DoesNotExist,
                          StockRecord.objects.get, id=stockrecord.id)
        self.assertRaises(ProductCategory.DoesNotExist,
                          ProductCategory.objects.get, id=product_category.id)
