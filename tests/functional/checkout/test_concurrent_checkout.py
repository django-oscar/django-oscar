from threading import Thread

from oscar.core.loading import get_model, get_class
from oscar.test.testcases import WebTestCase
from . import CheckoutMixin

Order = get_model('order', 'Order')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
UserAddress = get_model('address', 'UserAddress')
GatewayForm = get_class('checkout.forms', 'GatewayForm')


class TestConcurrectCheckout(CheckoutMixin, WebTestCase):

    def do_checkout(self, apply_voucher=False):
        self.add_product_to_basket()
        if apply_voucher:
            self.add_voucher_to_basket()
        self.enter_shipping_address()
        self.place_order()

    def test_num_allocated(self):
        t1 = Thread(target=self.do_checkout)
        t2 = Thread(target=self.do_checkout)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        order = Order.objects.last()
        stockrecord = order.lines.first().stockrecord
        self.assertEqual(2, stockrecord.num_allocated)
