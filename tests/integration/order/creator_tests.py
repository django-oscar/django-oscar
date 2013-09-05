from decimal import Decimal as D

from django.test import TestCase
from django.test.utils import override_settings
from mock import Mock

from oscar.apps.basket.models import Basket
from oscar.apps.catalogue.models import ProductClass, Product
from oscar.apps.offer.utils import Applicator
from oscar.apps.order.models import Order
from oscar.apps.order.utils import OrderCreator
from oscar.apps.shipping.methods import FixedPrice, Free
from oscar.apps.shipping.repository import Repository
from oscar.core.loading import get_class
from oscar.test.factories import create_product, create_offer

Range = get_class('offer.models', 'Range')
Benefit = get_class('offer.models', 'Benefit')


class TestOrderCreatorErrorCases(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = Basket()

    def test_raises_exception_when_empty_basket_passed(self):
        with self.assertRaises(ValueError):
            self.creator.place_order(basket=self.basket)

    def test_raises_exception_if_duplicate_order_number_passed(self):
        self.basket.add_product(create_product(price=D('12.00')))
        self.creator.place_order(basket=self.basket, order_number='1234')
        with self.assertRaises(ValueError):
            self.creator.place_order(basket=self.basket, order_number='1234')


class TestSuccessfulOrderCreation(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = Basket.objects.create()

    def tearDown(self):
        Order.objects.all().delete()

    def test_creates_order_and_line_models(self):
        self.basket.add_product(create_product(price=D('12.00')))
        self.creator.place_order(basket=self.basket, order_number='1234')
        order = Order.objects.get(number='1234')
        lines = order.lines.all()
        self.assertEqual(1, len(lines))

    def test_sets_correct_order_status(self):
        self.basket.add_product(create_product(price=D('12.00')))
        self.creator.place_order(basket=self.basket, order_number='1234', status='Active')
        order = Order.objects.get(number='1234')
        self.assertEqual('Active', order.status)

    def test_defaults_to_using_free_shipping(self):
        self.basket.add_product(create_product(price=D('12.00')))
        self.creator.place_order(basket=self.basket, order_number='1234')
        order = Order.objects.get(number='1234')
        self.assertEqual(order.total_incl_tax, self.basket.total_incl_tax)
        self.assertEqual(order.total_excl_tax, self.basket.total_excl_tax)

    def test_defaults_to_setting_totals_to_basket_totals(self):
        self.basket.add_product(create_product(price=D('12.00')))
        method = Mock()
        method.is_discounted = False
        method.basket_charge_incl_tax = Mock(return_value=D('2.00'))
        method.basket_charge_excl_tax = Mock(return_value=D('2.00'))

        self.creator.place_order(basket=self.basket, order_number='1234', shipping_method=method)
        order = Order.objects.get(number='1234')
        self.assertEqual(order.total_incl_tax, self.basket.total_incl_tax + D('2.00'))
        self.assertEqual(order.total_excl_tax, self.basket.total_excl_tax + D('2.00'))

    def test_uses_default_order_status_from_settings(self):
        self.basket.add_product(create_product(price=D('12.00')))
        with override_settings(OSCAR_INITIAL_ORDER_STATUS='A'):
            self.creator.place_order(basket=self.basket, order_number='1234')
        order = Order.objects.get(number='1234')
        self.assertEqual('A', order.status)

    def test_uses_default_line_status_from_settings(self):
        self.basket.add_product(create_product(price=D('12.00')))
        with override_settings(OSCAR_INITIAL_LINE_STATUS='A'):
            self.creator.place_order(basket=self.basket, order_number='1234')
        order = Order.objects.get(number='1234')
        line = order.lines.all()[0]
        self.assertEqual('A', line.status)


class TestPlacingOrderForDigitalGoods(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = Basket.objects.create()

    def test_does_not_allocate_stock(self):
        ProductClass.objects.create(
            name="Digital", track_stock=False)
        product = create_product(
            price=D('9.99'), product_class="Digital", num_in_stock=None)
        self.assertTrue(product.stockrecord.num_in_stock is None)
        self.assertTrue(product.stockrecord.num_allocated is None)

        self.basket.add_product(product)
        self.creator.place_order(basket=self.basket, order_number='1234')

        product_ = Product.objects.get(id=product.id)
        self.assertTrue(product_.stockrecord.num_in_stock is None)
        self.assertTrue(product_.stockrecord.num_allocated is None)

class StubRepository(Repository):
    """ Custom shipping methods """
    methods = (FixedPrice(D('5.00')), Free())

class TestShippingOfferForOrder(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = Basket.objects.create()

    def apply_20percent_shipping_offer(self):
        """Shipping offer 20% off"""
        range = Range.objects.create(name="All products range",
                                    includes_all_products=True)
        benefit = Benefit.objects.create(
            range=range, type=Benefit.SHIPPING_PERCENTAGE, value=20)
        offer = create_offer(range=range, benefit=benefit)
        Applicator().apply_offers(self.basket, [offer])

    def test_shipping_offer_is_applied(self):
        self.basket.add_product(create_product(price=D('12.00')))
        self.apply_20percent_shipping_offer()

        # Normal shipping 5.00
        shipping = StubRepository().find_by_code(FixedPrice.code, self.basket)

        self.creator.place_order(
            basket=self.basket,
            order_number='1234',
            shipping_method=shipping)
        order = Order.objects.get(number='1234')

        self.assertEqual(1, len(order.shipping_discounts))
        self.assertEqual(D('4.00'), order.shipping_incl_tax)
        self.assertEqual(D('16.00'), order.total_incl_tax)

    def test_zero_shipping_discount_is_not_created(self):
        self.basket.add_product(create_product(price=D('12.00')))
        self.apply_20percent_shipping_offer()

        # Free shipping
        shipping = StubRepository().find_by_code(Free.code, self.basket)

        self.creator.place_order(
            basket=self.basket,
            order_number='1234',
            shipping_method=shipping)
        order = Order.objects.get(number='1234')

        # No shipping discount
        self.assertEqual(0, len(order.shipping_discounts))
        self.assertEqual(D('0.00'), order.shipping_incl_tax)
        self.assertEqual(D('12.00'), order.total_incl_tax)
