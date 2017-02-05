from decimal import Decimal as D

from django.test import TestCase
from django.test.utils import override_settings

from oscar.apps.catalogue.models import ProductClass, Product
from oscar.apps.checkout import calculators
from oscar.apps.offer.utils import Applicator
from oscar.apps.order.models import Order
from oscar.apps.order.utils import OrderCreator
from oscar.apps.shipping.methods import Free, FixedPrice
from oscar.apps.shipping.repository import Repository
from oscar.core.loading import get_class
from oscar.test import factories
from oscar.test.basket import add_product

Range = get_class('offer.models', 'Range')
Benefit = get_class('offer.models', 'Benefit')


def place_order(creator, **kwargs):
    """
    Helper function to place an order without the boilerplate
    """
    if 'shipping_method' not in kwargs:
        kwargs['shipping_method'] = Free()

    shipping_charge = kwargs['shipping_method'].calculate(kwargs['basket'])
    kwargs['total'] = calculators.OrderTotalCalculator().calculate(
        basket=kwargs['basket'], shipping_charge=shipping_charge)
    kwargs['shipping_charge'] = shipping_charge

    return creator.place_order(**kwargs)


class TestOrderCreatorErrorCases(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = factories.create_basket(empty=True)

    def test_raises_exception_when_empty_basket_passed(self):
        with self.assertRaises(ValueError):
            place_order(self.creator, basket=self.basket)

    def test_raises_exception_if_duplicate_order_number_passed(self):
        add_product(self.basket, D('12.00'))
        place_order(self.creator, basket=self.basket, order_number='1234')
        with self.assertRaises(ValueError):
            place_order(self.creator, basket=self.basket, order_number='1234')


class TestSuccessfulOrderCreation(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = factories.create_basket(empty=True)

    def test_saves_shipping_code(self):
        add_product(self.basket, D('12.00'))
        free_method = Free()
        order = place_order(self.creator, basket=self.basket,
                            order_number='1234', shipping_method=free_method)
        self.assertEqual(order.shipping_code, free_method.code)

    def test_creates_order_and_line_models(self):
        add_product(self.basket, D('12.00'))
        place_order(self.creator, basket=self.basket, order_number='1234')
        order = Order.objects.get(number='1234')
        lines = order.lines.all()
        self.assertEqual(1, len(lines))

    def test_sets_correct_order_status(self):
        add_product(self.basket, D('12.00'))
        place_order(self.creator, basket=self.basket,
                    order_number='1234', status='Active')
        order = Order.objects.get(number='1234')
        self.assertEqual('Active', order.status)

    def test_defaults_to_using_free_shipping(self):
        add_product(self.basket, D('12.00'))
        place_order(self.creator, basket=self.basket, order_number='1234')
        order = Order.objects.get(number='1234')
        self.assertEqual(order.total_incl_tax, self.basket.total_incl_tax)
        self.assertEqual(order.total_excl_tax, self.basket.total_excl_tax)

    def test_uses_default_order_status_from_settings(self):
        add_product(self.basket, D('12.00'))
        with override_settings(OSCAR_INITIAL_ORDER_STATUS='A'):
            place_order(self.creator, basket=self.basket, order_number='1234')
        order = Order.objects.get(number='1234')
        self.assertEqual('A', order.status)

    def test_uses_default_line_status_from_settings(self):
        add_product(self.basket, D('12.00'))
        with override_settings(OSCAR_INITIAL_LINE_STATUS='A'):
            place_order(self.creator, basket=self.basket, order_number='1234')
        order = Order.objects.get(number='1234')
        line = order.lines.all()[0]
        self.assertEqual('A', line.status)

    def test_partner_name_is_optional(self):
        for partner_name, order_number in [('', 'A'), ('p1', 'B')]:
            self.basket = factories.create_basket(empty=True)
            product = factories.create_product(partner_name=partner_name)
            add_product(self.basket, D('12.00'), product=product)
            place_order(
                self.creator, basket=self.basket, order_number=order_number)
            line = Order.objects.get(number=order_number).lines.all()[0]
            partner = product.stockrecords.all()[0].partner
            self.assertTrue(partner_name == line.partner_name == partner.name)


class TestPlacingOrderForDigitalGoods(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = factories.create_basket(empty=True)

    def test_does_not_allocate_stock(self):
        ProductClass.objects.create(
            name="Digital", track_stock=False)
        product = factories.create_product(product_class="Digital")
        record = factories.create_stockrecord(product, num_in_stock=None)
        self.assertTrue(record.num_allocated is None)

        add_product(self.basket, D('12.00'), product=product)
        place_order(self.creator, basket=self.basket, order_number='1234')

        product = Product.objects.get(id=product.id)
        stockrecord = product.stockrecords.all()[0]
        self.assertTrue(stockrecord.num_in_stock is None)
        self.assertTrue(stockrecord.num_allocated is None)


class TestShippingOfferForOrder(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = factories.create_basket(empty=True)

    def apply_20percent_shipping_offer(self):
        """Shipping offer 20% off"""
        range = Range.objects.create(name="All products range",
                                     includes_all_products=True)
        benefit = Benefit.objects.create(
            range=range, type=Benefit.SHIPPING_PERCENTAGE, value=20)
        offer = factories.create_offer(range=range, benefit=benefit)
        Applicator().apply_offers(self.basket, [offer])
        return offer

    def test_shipping_offer_is_applied(self):
        add_product(self.basket, D('12.00'))
        offer = self.apply_20percent_shipping_offer()

        shipping = FixedPrice(D('5.00'), D('5.00'))
        shipping = Repository().apply_shipping_offer(
            self.basket, shipping, offer)

        place_order(self.creator,
                    basket=self.basket,
                    order_number='1234',
                    shipping_method=shipping)
        order = Order.objects.get(number='1234')

        self.assertEqual(1, len(order.shipping_discounts))
        self.assertEqual(D('4.00'), order.shipping_incl_tax)
        self.assertEqual(D('16.00'), order.total_incl_tax)

    def test_zero_shipping_discount_is_not_created(self):
        add_product(self.basket, D('12.00'))
        offer = self.apply_20percent_shipping_offer()

        shipping = Free()
        shipping = Repository().apply_shipping_offer(
            self.basket, shipping, offer)

        place_order(self.creator,
                    basket=self.basket,
                    order_number='1234',
                    shipping_method=shipping)
        order = Order.objects.get(number='1234')

        # No shipping discount
        self.assertEqual(0, len(order.shipping_discounts))
        self.assertEqual(D('0.00'), order.shipping_incl_tax)
        self.assertEqual(D('12.00'), order.total_incl_tax)


class TestMultiSiteOrderCreation(TestCase):

    def setUp(self):
        self.creator = OrderCreator()
        self.basket = factories.create_basket(empty=True)

    def test_default_site(self):
        add_product(self.basket, D('12.00'))
        place_order(self.creator,
                    basket=self.basket,
                    order_number='1234')
        order = Order.objects.get(number='1234')
        self.assertEqual(order.site_id, 1)

    def test_multi_sites(self):
        site1 = factories.SiteFactory()
        site2 = factories.SiteFactory()
        add_product(self.basket, D('12.00'))
        place_order(self.creator,
                    basket=self.basket,
                    order_number='12345',
                    site=site1)
        order1 = Order.objects.get(number='12345')
        self.assertEqual(order1.site, site1)
        add_product(self.basket, D('12.00'))
        place_order(self.creator,
                    basket=self.basket,
                    order_number='12346',
                    site=site2)
        order2 = Order.objects.get(number='12346')
        self.assertEqual(order2.site, site2)
