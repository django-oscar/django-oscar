from django.contrib.auth.models import Permission
from django.db.models import get_model
from django.core.urlresolvers import reverse

from oscar.test.testcases import ClientTestCase
from oscar.test.factories import create_product

from django_dynamic_fixture import G
from oscar.test.testcases import WebTestCase

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
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

    def test_can_create_a_product_without_stockrecord(self):
        category = G(Category)
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.id,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['productcategory_set-0-category'] = category.id
        page = form.submit()

        self.assertEquals(Product.objects.count(), 1)

    def test_can_create_and_continue_editing_a_product(self):
        category = G(Category)
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.id,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['productcategory_set-0-category'] = category.id
        page = form.submit('action', index=0)

        self.assertEquals(Product.objects.count(), 1)

        product = Product.objects.all()[0]
        self.assertRedirects(page, reverse('dashboard:catalogue-product',
                                           kwargs={'pk': product.id}))

    def test_can_update_a_product_without_stockrecord(self):
        new_title = u'foobar'
        category = G(Category)
        product = G(Product, ignore_fields=['stockrecord'], parent=None)

        page = self.get(
            reverse('dashboard:catalogue-product',
                    kwargs={'pk': product.id})
        )
        form = page.forms[0]
        form['productcategory_set-0-category'] = category.id
        assert form['partner'].value == u''
        assert form['title'].value != new_title
        form['title'] = new_title

        form.submit()

        try:
            product = Product.objects.get(pk=product.pk)
        except Product.DoesNotExist:
            pass
        else:
            self.assertTrue(product.title == new_title)
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

class TestANonStaffUser(TestAStaffUser):
    is_staff = False
    is_anonymous = False
    permissions = ['partner.dashboard_access', 'catalogue.change_product']

    def setUp(self):
        super(TestANonStaffUser, self).setUp()
        self.add_permissions()

    def add_permissions(self):
        for permission in self.permissions:
            app_label, _, codename = permission.partition('.')
            perm = Permission.objects.get(content_type__app_label=app_label,
                                          codename=codename)
            self.user.user_permissions.add(perm)
