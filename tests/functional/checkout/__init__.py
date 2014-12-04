from decimal import Decimal as D

from django.core.urlresolvers import reverse

from oscar.apps.address.models import Country
from oscar.test import factories


class CheckoutMixin(object):

    def create_digital_product(self):
        product = factories.create_product(price=D('12.00'), num_in_stock=None)
        product.product_class.requires_shipping = False
        product.product_class.track_stock = False
        product.product_class.save()
        return product

    def add_product_to_basket(self, product=None):
        if product is None:
            product = factories.create_product(price=D('12.00'),
                                               num_in_stock=10)
        detail_page = self.get(product.get_absolute_url())
        form = detail_page.forms['add_to_basket_form']
        form.submit()

    def add_voucher_to_basket(self, voucher=None):
        if voucher is None:
            voucher = factories.create_voucher()
        basket_page = self.get(reverse('basket:summary'))
        form = basket_page.forms['voucher_form']
        form['code'] = voucher.code
        form.submit()

    def enter_guest_details(self, email='guest@example.com'):
        index_page = self.get(reverse('checkout:index'))
        index_page.form['username'] = email
        index_page.form.submit()

    def create_shipping_country(self):
        Country.objects.get_or_create(
            iso_3166_1_a2='GB', is_shipping_country=True)

    def enter_shipping_address(self):
        self.create_shipping_country()
        address_page = self.get(reverse('checkout:shipping-address'))
        form = address_page.forms['new_shipping_address']
        form['first_name'] = 'John'
        form['last_name'] = 'Doe'
        form['line1'] = '1 Egg Road'
        form['line4'] = 'Shell City'
        form['postcode'] = 'N12 9RT'
        form.submit()

    def enter_shipping_method(self):
        self.get(reverse('checkout:shipping-method'))

    def place_order(self):
        payment_details = self.get(
            reverse('checkout:shipping-method')).follow().follow()
        preview = payment_details.click(linkid="view_preview")
        return preview.forms['place_order_form'].submit().follow()
