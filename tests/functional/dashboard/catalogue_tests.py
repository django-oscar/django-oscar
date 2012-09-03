from django.db.models import get_model
from django.core.urlresolvers import reverse

from oscar.test import ClientTestCase

from django_webtest import WebTest
from django_dynamic_fixture import G

User = get_model('auth', 'user')
Product = get_model('catalogue', 'product')
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


class TestCatalogueDashboardViews(WebTest):
    email = 'test@test.com'
    password = 'mypassword'

    def setUp(self):
        print 'setting up test'
        user = User.objects.create_user('_', self.email, self.password)
        user.is_staff = True
        user.save()

        form = self.app.get(reverse('customer:login')).forms['login_form']
        form['login-username'] = self.email
        form['login-password'] = self.password
        form.submit('login_submit')

    def test_can_login(self):
        product = G(Product, ignore_fields=['stockrecord'])

        form = self.app.get(
            reverse('dashboard:catalogue-product',
                    kwargs={'pk': product.id})
        ).forms[0]
        assert form['partner'].value == u''

        form.submit()

        try:
            product = Product.objects.get(pk=product.pk)
            product.stockrecord
            self.fail('product has stock record but should not')
        except StockRecord.DoesNotExist:
            pass
