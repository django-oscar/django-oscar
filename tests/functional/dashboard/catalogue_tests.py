from django.core.urlresolvers import reverse
from django.utils.six.moves import http_client

from oscar.core.loading import get_model
from oscar.test.testcases import WebTestCase, add_permissions
from oscar.test.factories import create_product
from oscar.test.factories import (
    CategoryFactory, PartnerFactory, ProductFactory, ProductAttributeFactory)

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductCategory = get_model('catalogue', 'ProductCategory')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'stockrecord')


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
        self.partner = PartnerFactory()

    def test_can_create_a_product_without_stockrecord(self):
        category = CategoryFactory()
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['productcategory_set-0-category'] = category.id
        form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_create_and_continue_editing_a_product(self):
        category = CategoryFactory()
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
        page = form.submit(name='action', value='continue')

        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.all()[0]
        self.assertEqual(product.stockrecords.all()[0].partner, self.partner)
        self.assertRedirects(page, reverse('dashboard:catalogue-product',
                                           kwargs={'pk': product.id}))

    def test_can_update_a_product_without_stockrecord(self):
        new_title = u'foobar'
        category = CategoryFactory()
        product = ProductFactory(stockrecords=[])

        page = self.get(
            reverse('dashboard:catalogue-product',
                    kwargs={'pk': product.id})
        )
        form = page.forms[0]
        form['productcategory_set-0-category'] = category.id
        self.assertNotEqual(form['title'].value, new_title)
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

    def test_can_create_product_with_required_attributes(self):
        category = CategoryFactory()
        attribute = ProductAttributeFactory(required=True)
        product_class = attribute.product_class
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['attr_weight'] = '5'
        form['productcategory_set-0-category'] = category.id
        form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_delete_a_standalone_product(self):
        product = create_product(partner_users=[self.user])
        category = Category.add_root(name='Test Category')
        ProductCategory.objects.create(category=category, product=product)

        page = self.get(reverse('dashboard:catalogue-product-delete',
                                args=(product.id,))).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-product-list'))
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(StockRecord.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(ProductCategory.objects.count(), 0)

    def test_can_delete_a_parent_product(self):
        parent_product = create_product(structure='parent')
        create_product(parent=parent_product)

        url = reverse(
            'dashboard:catalogue-product-delete',
            args=(parent_product.id,))
        page = self.get(url).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-product-list'))
        self.assertEqual(Product.objects.count(), 0)

    def test_can_delete_a_child_product(self):
        parent_product = create_product(structure='parent')
        child_product = create_product(parent=parent_product)

        url = reverse(
            'dashboard:catalogue-product-delete',
            args=(child_product.id,))
        page = self.get(url).form.submit()

        expected_url = reverse(
            'dashboard:catalogue-product', kwargs={'pk': parent_product.pk})
        self.assertRedirects(page, expected_url)
        self.assertEqual(Product.objects.count(), 1)

    def test_can_list_her_products(self):
        product1 = create_product(partner_users=[self.user, ])
        product2 = create_product(partner_name="sneaky", partner_users=[])
        page = self.get(reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)

    def test_can_create_a_child_product(self):
        parent_product = create_product(structure='parent')
        url = reverse(
            'dashboard:catalogue-product-create-child',
            kwargs={'parent_pk': parent_product.pk})
        form = self.get(url).form
        form.submit()

        self.assertEqual(Product.objects.count(), 2)

    def test_cant_create_child_product_for_invalid_parents(self):
        # Creates a product with stockrecords.
        invalid_parent = create_product(partner_users=[self.user])
        self.assertFalse(invalid_parent.can_be_parent())
        url = reverse(
            'dashboard:catalogue-product-create-child',
            kwargs={'parent_pk': invalid_parent.pk})
        self.assertRedirects(
            self.get(url), reverse('dashboard:catalogue-product-list'))


class TestANonStaffUser(TestAStaffUser):
    is_staff = False
    is_anonymous = False
    permissions = ['partner.dashboard_access', ]

    def setUp(self):
        super(TestANonStaffUser, self).setUp()
        add_permissions(self.user, self.permissions)
        self.partner.users.add(self.user)

    def test_can_list_her_products(self):
        product1 = create_product(partner_name="A", partner_users=[self.user])
        product2 = create_product(partner_name="B", partner_users=[])
        page = self.get(reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)

    def test_cant_create_a_child_product(self):
        parent_product = create_product(structure='parent')
        url = reverse(
            'dashboard:catalogue-product-create-child',
            kwargs={'parent_pk': parent_product.pk})
        response = self.get(url, status='*')
        self.assertEqual(http_client.FORBIDDEN, response.status_code)

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
