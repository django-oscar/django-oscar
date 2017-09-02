from decimal import Decimal as D
import threading
import time

import pytest
from django.http import HttpRequest
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser

from oscar.apps.catalogue.models import ProductClass, Product
from oscar.apps.checkout import calculators
from oscar.apps.offer.utils import Applicator
from oscar.apps.order.models import Order
from oscar.apps.order.utils import OrderCreator
from oscar.apps.shipping.methods import Free, FixedPrice
from oscar.apps.shipping.repository import Repository
from oscar.apps.voucher.models import Voucher
from oscar.core.loading import get_class
from oscar.test import factories
from oscar.test.basket import add_product
from tests.utils import run_concurrently

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
        self.site1 = factories.SiteFactory()
        self.site2 = factories.SiteFactory()

    def test_default_site(self):
        add_product(self.basket, D('12.00'))
        place_order(self.creator,
                    basket=self.basket,
                    order_number='1234')
        order = Order.objects.get(number='1234')
        self.assertEqual(order.site_id, 1)

    def test_multi_sites(self):
        add_product(self.basket, D('12.00'))
        place_order(self.creator,
                    basket=self.basket,
                    order_number='12345',
                    site=self.site1)
        order1 = Order.objects.get(number='12345')
        self.assertEqual(order1.site, self.site1)
        add_product(self.basket, D('12.00'))
        place_order(self.creator,
                    basket=self.basket,
                    order_number='12346',
                    site=self.site2)
        order2 = Order.objects.get(number='12346')
        self.assertEqual(order2.site, self.site2)

    @override_settings(SITE_ID='')
    def test_request(self):
        request = HttpRequest()
        request.META['SERVER_PORT'] = 80
        request.META['SERVER_NAME'] = self.site1.domain
        add_product(self.basket, D('12.00'))
        place_order(self.creator,
                    basket=self.basket,
                    order_number='12345',
                    request=request)
        order1 = Order.objects.get(number='12345')
        self.assertEqual(order1.site, self.site1)
        add_product(self.basket, D('12.00'))
        request.META['SERVER_NAME'] = self.site2.domain
        place_order(self.creator,
                    basket=self.basket,
                    order_number='12346',
                    request=request)
        order2 = Order.objects.get(number='12346')
        self.assertEqual(order2.site, self.site2)


class TestPlaceOrderWithVoucher(TestCase):

    def test_single_usage(self):
        user = AnonymousUser()
        basket = factories.create_basket()
        creator = OrderCreator()

        voucher = factories.VoucherFactory(usage=Voucher.SINGLE_USE)
        voucher.offers.add(factories.create_offer(offer_type='Voucher'))
        basket.vouchers.add(voucher)

        place_order(creator, basket=basket, order_number='12346', user=user)
        assert voucher.applications.count() == 1

        # Make sure the voucher usage is rechecked
        with pytest.raises(ValueError):
            place_order(creator, basket=basket, order_number='12347', user=user)


class TestConcurrentOrderPlacement(TransactionTestCase):

    def test_single_usage(self):
        user = AnonymousUser()
        creator = OrderCreator()
        product = factories.ProductFactory(stockrecords__num_in_stock=1000)

        # Make the order creator a bit more slow too reliable trigger
        # concurrency issues
        org_create_order_model = OrderCreator.create_order_model

        def new_create_order_model(*args, **kwargs):
            time.sleep(0.5)
            return org_create_order_model(creator, *args, **kwargs)
        creator.create_order_model = new_create_order_model

        # Start 5 threads to place an order concurrently
        def worker():
            order_number = threading.current_thread().name

            basket = factories.BasketFactory()
            basket.add_product(product)
            place_order(
                creator, basket=basket, order_number=order_number, user=user)

        exceptions = run_concurrently(worker, num_threads=5)

        assert all(isinstance(x, ValueError) for x in exceptions), exceptions
        assert len(exceptions) == 0
        assert Order.objects.count() == 5

        stockrecord = product.stockrecords.first()
        assert stockrecord.num_allocated == 5

    def test_voucher_single_usage(self):
        user = AnonymousUser()
        creator = OrderCreator()
        product = factories.ProductFactory()
        voucher = factories.VoucherFactory(usage=Voucher.SINGLE_USE)
        voucher.offers.add(factories.create_offer(offer_type='Voucher'))

        # Make the order creator a bit more slow too reliable trigger
        # concurrency issues
        org_create_order_model = OrderCreator.create_order_model

        def new_create_order_model(*args, **kwargs):
            time.sleep(0.5)
            return org_create_order_model(creator, *args, **kwargs)
        creator.create_order_model = new_create_order_model

        org_record_voucher_usage = OrderCreator.record_voucher_usage

        def record_voucher_usage(*args, **kwargs):
            time.sleep(0.5)
            return org_record_voucher_usage(creator, *args, **kwargs)
        creator.record_voucher_usage = record_voucher_usage

        # Start 5 threads to place an order concurrently
        def worker():
            order_number = threading.current_thread().name

            basket = factories.BasketFactory()
            basket.add_product(product)
            basket.vouchers.add(voucher)
            place_order(
                creator, basket=basket, order_number=order_number, user=user)

        exceptions = run_concurrently(worker, num_threads=5)

        voucher.refresh_from_db()
        assert all(isinstance(x, ValueError) for x in exceptions), exceptions
        assert len(exceptions) == 4
        assert voucher.applications.count() == 1

        assert Order.objects.count() == 1
