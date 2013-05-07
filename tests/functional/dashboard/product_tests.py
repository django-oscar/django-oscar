from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G

from oscar_testsupport.testcases import WebTestCase
from oscar.apps.catalogue.models import ProductClass, Category, Product


class ProductWebTest(WebTestCase):
    is_staff = True

    def setUp(self):
        self.user = User.objects.create_user(username='testuser',
                                             email='test@email.com',
                                             password='somefancypassword')
        self.user.is_staff = self.is_staff
        self.user.save()

    def get(self, url, **kwargs):
        kwargs['user'] = self.user
        return self.app.get(url, **kwargs)


class TestGatewayPage(ProductWebTest):
    is_staff = True

    def test_redirects_to_list_page_when_no_query_param(self):
        url = reverse('dashboard:catalogue-product-create')
        response = self.get(url)
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-product-list'))

    def test_redirects_to_list_page_when_invalid_query_param(self):
        url = reverse('dashboard:catalogue-product-create')
        response = self.get(url + '?product_class=bad')
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-product-list'))

    def test_redirects_to_form_page_when_valid_query_param(self):
        pclass = G(ProductClass)
        url = reverse('dashboard:catalogue-product-create')
        response = self.get(url + '?product_class=%d' % pclass.id)
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-product-create',
                                     kwargs={'product_class_id': pclass.id}))


class TestCreateGroupProduct(ProductWebTest):
    is_staff = True

    def setUp(self):
        self.pclass = G(ProductClass)
        super(TestCreateGroupProduct, self).setUp()

    def submit(self, title=None, category=None, upc=None):
        url = reverse('dashboard:catalogue-product-create',
                      kwargs={'product_class_id': self.pclass.id})

        product_form = self.get(url).form

        product_form['title'] = title
        product_form['upc'] = upc

        if category:
            product_form['productcategory_set-0-category'] = category.id

        return product_form.submit()

    def test_title_is_required(self):
        response = self.submit(title='')

        self.assertContains(response, "Parent products must have a title")
        self.assertEquals(Product.objects.count(), 0)

    def test_requires_a_category(self):
        response = self.submit(title="Nice T-Shirt")
        self.assertContains(response,
            "A top-level product must have at least one category")
        self.assertEquals(Product.objects.count(), 0)

    def test_doesnt_smoke(self):
        category = G(Category)
        response = self.submit(category=category)

        self.assertContains(response, "Parent products must have a title")
        self.assertEquals(Product.objects.count(), 0)

    def test_doesnt_allow_duplicate_upc(self):
        G(Product, parent=None, upc="12345")
        category = G(Category)
        self.assertTrue(Product.objects.get(upc="12345"))

        response = self.submit(title="Nice T-Shirt", category=category,
                               upc="12345")

        self.assertEquals(Product.objects.count(), 1)
        self.assertNotEquals(Product.objects.get(upc='12345').title,
                             'Nice T-Shirt')
        self.assertContains(response,
                            "Product with this UPC already exists.")


class TestCreateChildProduct(ProductWebTest):
    is_staff = True

    def setUp(self):
        self.pclass = G(ProductClass)
        self.parent = G(Product)
        super(TestCreateChildProduct, self).setUp()

    def test_categories_are_not_required(self):
        url = reverse('dashboard:catalogue-product-create',
                      kwargs={'product_class_id': self.pclass.id})
        page = self.get(url)

        product_form = page.form
        product_form['title'] = 'Nice T-Shirt'
        product_form['parent'] = self.parent.id
        page = product_form.submit()

        try:
            product = Product.objects.get(title='Nice T-Shirt')
        except Product.DoesNotExist:
            self.fail('creating a child product did not work: %s' % page.body)

        self.assertEquals(product.parent, self.parent)
