from django.core.urlresolvers import reverse
from django_dynamic_fixture import G

from oscar.test import ClientTestCase
from oscar.apps.catalogue.models import ProductClass, Category, Product


class TestGatewayPage(ClientTestCase):
    is_staff = True

    def test_redirects_to_list_page_when_no_query_param(self):
        url = reverse('dashboard:catalogue-product-create')
        response = self.client.get(url)
        self.assertRedirectUrlName(response,
                                   'dashboard:catalogue-product-list')

    def test_redirects_to_list_page_when_invalid_query_param(self):
        url = reverse('dashboard:catalogue-product-create')
        response = self.client.get(url + '?product_class=bad')
        self.assertRedirectUrlName(response,
                                   'dashboard:catalogue-product-list')

    def test_redirects_to_form_page_when_valid_query_param(self):
        pclass = G(ProductClass)
        url = reverse('dashboard:catalogue-product-create')
        response = self.client.get(url + '?product_class=%d' % pclass.id)
        self.assertRedirectUrlName(response,
                                   'dashboard:catalogue-product-create',
                                   {'product_class_id': pclass.id})


class TestCreateGroupProduct(ClientTestCase):
    is_staff = True

    def setUp(self):
        self.pclass = G(ProductClass)
        super(TestCreateGroupProduct, self).setUp()

    def submit(self, **params):
        data = {'title': 'Nice T-Shirt',
                'productcategory_set-TOTAL_FORMS': '1',
                'productcategory_set-INITIAL_FORMS': '0',
                'productcategory_set-MAX_NUM_FORMS': '',
                'images-TOTAL_FORMS': '2',
                'images-INITIAL_FORMS': '0',
                'images-MAX_NUM_FORMS': '',
               }
        data.update(params)
        url = reverse('dashboard:catalogue-product-create',
                      kwargs={'product_class_id': self.pclass.id})
        return self.client.post(url, data)

    def test_title_is_required(self):
        response = self.submit(title='')
        self.assertIsOk(response)

    def test_requires_a_category(self):
        response = self.submit()
        self.assertIsOk(response)

    def test_doesnt_smoke(self):
        category = G(Category)
        data = {
            'productcategory_set-0-category': category.id,
            'productcategory_set-0-id': '',
            'productcategory_set-0-product': '',
        }
        response = self.submit(**data)
        self.assertRedirectUrlName(response, 'dashboard:catalogue-product-list')


class TestCreateChildProduct(ClientTestCase):
    is_staff = True

    def setUp(self):
        self.pclass = G(ProductClass)
        self.parent = G(Product)
        super(TestCreateChildProduct, self).setUp()

    def submit(self, **params):
        data = {'title': 'Nice T-Shirt',
                'productcategory_set-TOTAL_FORMS': '1',
                'productcategory_set-INITIAL_FORMS': '0',
                'productcategory_set-MAX_NUM_FORMS': '',
                'images-TOTAL_FORMS': '2',
                'images-INITIAL_FORMS': '0',
                'images-MAX_NUM_FORMS': '',
               }
        data.update(params)
        url = reverse('dashboard:catalogue-product-create',
                      kwargs={'product_class_id': self.pclass.id})
        return self.client.post(url, data)

    def test_categories_are_not_required(self):
        category = G(Category)
        data = {
            'parent': self.parent.id,
            'productcategory_set-0-category': category.id,
            'productcategory_set-0-id': '',
            'productcategory_set-0-product': '',
        }
        response = self.submit(**data)
        self.assertIsOk(response)
