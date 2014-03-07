from oscar.core.loading import get_model
from django.core.urlresolvers import reverse

from oscar.test.testcases import WebTestCase, add_permissions
from oscar.test.factories import create_product, create_stockrecord

from django_dynamic_fixture import G

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductCategory = get_model('catalogue', 'ProductCategory')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'stockrecord')
Partner = get_model('partner', 'partner')


class TestCatalogueViews(WebTestCase):
    is_staff = True

    def test_exist(self):
        urls = [reverse('dashboard:catalogue-product-list'),
                reverse('dashboard:catalogue-category-list'),
                reverse('dashboard:stock-alert-list')]
        for url in urls:
            self.assertIsOk(self.get(url))


class TestAStaffUser(WebTestCase):
    is_staff = True

    def setUp(self):
        super(TestAStaffUser, self).setUp()
        self.partner = G(Partner)

    def test_can_create_a_product_without_stockrecord(self):
        category = G(Category)
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['productcategory_set-0-category'] = category.id
        page = form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_create_and_continue_editing_a_product(self):
        category = G(Category)
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['productcategory_set-0-category'] = category.id
        form['stockrecords-0-partner'] = self.partner.id
        form['stockrecords-0-partner_sku'] = '14'
        form['stockrecords-0-num_in_stock'] = '555'
        form['stockrecords-0-price_excl_tax'] = '13.99'
        page = form.submit('action', index=0)

        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.all()[0]
        self.assertEqual(product.stockrecords.all()[0].partner, self.partner)
        self.assertRedirects(page, reverse('dashboard:catalogue-product',
                                           kwargs={'pk': product.id}))

    def test_can_update_a_product_without_stockrecord(self):
        new_title = u'foobar'
        category = G(Category)
        product = G(Product, parent=None)

        page = self.get(
            reverse('dashboard:catalogue-product',
                    kwargs={'pk': product.id})
        )
        form = page.forms[0]
        form['productcategory_set-0-category'] = category.id
        assert form['title'].value != new_title
        form['title'] = new_title
        form.submit()

        try:
            product = Product.objects.get(pk=product.pk)
        except Product.DoesNotExist:
            pass
        else:
            self.assertTrue(product.title == new_title)
            if product.has_stockrecords:
                self.fail('Product has stock records but should not')

    def test_can_delete_an_individual_product(self):
        product = create_product()
        stockrecord = create_stockrecord(product, partner_users=[self.user, ])

        category = Category.add_root(name='Test Category')
        product_category = ProductCategory.objects.create(category=category,
                                                          product=product)

        page = self.get(reverse('dashboard:catalogue-product-delete',
                                args=(product.id,))).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-product-list'))

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(StockRecord.objects.count(), 0)
        self.assertEqual(ProductCategory.objects.count(), 0)

        self.assertRaises(Product.DoesNotExist,
                          Product.objects.get, id=product.id)
        self.assertRaises(StockRecord.DoesNotExist,
                          StockRecord.objects.get, id=stockrecord.id)
        self.assertRaises(ProductCategory.DoesNotExist,
                          ProductCategory.objects.get, id=product_category.id)

    def test_can_delete_a_canonical_product(self):
        canonical_product = create_product(title="Canonical Product",
                                           partner_users=[self.user,])

        product = create_product(title="Variant 1", parent=canonical_product)
        stockrecord = create_stockrecord(product)

        category = Category.add_root(name='Test Category')
        product_category = ProductCategory.objects.create(
            category=category, product=product)

        page = self.get(reverse('dashboard:catalogue-product-delete',
                                args=(canonical_product.id,))).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-product-list'))

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(StockRecord.objects.count(), 0)
        self.assertEqual(ProductCategory.objects.count(), 0)

        self.assertRaises(Product.DoesNotExist,
                          Product.objects.get, id=canonical_product.id)

        self.assertRaises(Product.DoesNotExist,
                          Product.objects.get, id=product.id)
        self.assertRaises(StockRecord.DoesNotExist,
                          StockRecord.objects.get, id=stockrecord.id)
        self.assertRaises(ProductCategory.DoesNotExist,
                          ProductCategory.objects.get, id=product_category.id)

    def test_can_list_her_products(self):
        product1 = create_product(partner_users=[self.user, ])
        product2 = create_product(partner="sneaky", partner_users=[])
        page = self.get(reverse('dashboard:catalogue-product-list'))
        assert product1 in page.context['object_list']
        assert product2 in page.context['object_list']


class TestANonStaffUser(TestAStaffUser):
    is_staff = False
    is_anonymous = False
    permissions = ['partner.dashboard_access', ]

    def setUp(self):
        super(TestANonStaffUser, self).setUp()
        add_permissions(self.user, self.permissions)
        self.partner.users.add(self.user)

    def test_can_list_her_products(self):
        product1 = create_product(partner="A", partner_users=[self.user, ])
        product2 = create_product(partner="B", partner_users=[])
        page = self.get(reverse('dashboard:catalogue-product-list'))
        assert product1 in page.context['object_list']
        assert product2 not in page.context['object_list']

    def test_can_create_a_product_without_stockrecord(self):
        pass

    def test_can_update_a_product_without_stockrecord(self):
        pass

    def test_can_submit_an_invalid_product_update_and_returns_to_update_page(self):
        pass


