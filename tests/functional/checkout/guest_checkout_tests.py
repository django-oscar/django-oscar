from decimal import Decimal as D
import sys

from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.importlib import import_module

from oscar.test.testcases import WebTestCase
from oscar.test import factories

# Python 3 compat
try:
    from imp import reload
except ImportError:
    pass


def reload_url_conf():
    # Reload URLs to pick up the overridden settings
    if settings.ROOT_URLCONF in sys.modules:
        reload(sys.modules[settings.ROOT_URLCONF])
    import_module(settings.ROOT_URLCONF)


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestIndexView(WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestIndexView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:index'))
        self.assertRedirectUrlName(response, 'basket:summary')


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestShippingAddressView(WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestShippingAddressView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        product = factories.create_product(price=D('12.00'), num_in_stock=10)
        detail_page = self.get(product.get_absolute_url())
        form = detail_page.forms['add_to_basket_form']
        form.submit()

        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectUrlName(response, 'checkout:index')

    def test_redirects_customers_whose_basket_doesnt_require_shipping(self):
        # Create a product that doesn't require shipping
        product = factories.create_product(price=D('12.00'), num_in_stock=10)
        product.product_class.requires_shipping = False
        product.product_class.save()

        # Add product to basket
        detail_page = self.get(product.get_absolute_url())
        form = detail_page.forms['add_to_basket_form']
        form.submit()

        # Complete guest checkout
        index_page = self.get(reverse('checkout:index'))
        index_page.form['username'] = 'guest@example.com'
        index_page.form.submit()

        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectUrlName(response, 'checkout:shipping-method')
