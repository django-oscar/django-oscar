from decimal import Decimal as D
import random
import datetime

from oscar.apps.partner import strategy, availability, prices
from oscar.core.loading import get_class, get_classes

Basket = get_class('basket.models', 'Basket')
Free = get_class('shipping.methods', 'Free')
Voucher = get_class('voucher.models', 'Voucher')
OrderCreator = get_class('order.utils', 'OrderCreator')
OrderTotalCalculator = get_class('checkout.calculators',
                                 'OrderTotalCalculator')
Partner, StockRecord = get_classes('partner.models', ('Partner',
                                                      'StockRecord'))
(ProductClass,
 Product,
 ProductAttribute,
 ProductAttributeValue) = get_classes('catalogue.models',
                                      ('ProductClass',
                                       'Product',
                                       'ProductAttribute',
                                       'ProductAttributeValue'))
(Range,
 ConditionalOffer,
 Condition,
 Benefit) = get_classes('offer.models', ('Range', 'ConditionalOffer',
                                         'Condition', 'Benefit'))


def create_stockrecord(product=None, price_excl_tax=None, partner_sku=None,
                       num_in_stock=None, partner_name="Dummy partner"):
    if product is None:
        product = create_product()
    partner, __ = Partner.objects.get_or_create(
        name=partner_name)
    if not price_excl_tax:
        price_excl_tax = D('9.99')
    if not partner_sku:
        partner_sku = 'sku_%d_%d' % (product.id, random.randint(0, 10000))
    return product.stockrecords.create(
        partner=partner, partner_sku=partner_sku,
        price_excl_tax=price_excl_tax, num_in_stock=num_in_stock)


def create_stockinfo(record):
    return strategy.StockInfo(
        price=prices.DelegateToStockRecord(record),
        availability=availability.DelegateToStockRecord(record),
        stockrecord=record
    )


def create_product(upc=None, title=u"Dummy title",
                   product_class=u"Dummy item class",
                   partner=u"Dummy partner", partner_sku=None, price=None,
                   num_in_stock=None, attributes=None, **kwargs):
    """
    Helper method for creating products that are used in tests.
    """
    product_class, __ = ProductClass._default_manager.get_or_create(
        name=product_class)
    product = product_class.products.model(
        product_class=product_class,
        title=title, upc=upc, **kwargs)
    if attributes:
        for code, value in attributes.items():
            # Ensure product attribute exists
            product_class.attributes.get_or_create(
                name=code, code=code)
            setattr(product.attr, code, value)
    product.save()

    # Shortcut for creating stockrecord
    if price is not None or partner_sku or num_in_stock is not None:
        create_stockrecord(product, price_excl_tax=price,
                           partner_sku=partner_sku, num_in_stock=num_in_stock)
    return product


def create_basket():
    basket = Basket.objects.create()
    product = create_product()
    stockrecord = create_stockrecord(product)
    stockinfo = create_stockinfo(stockrecord)
    basket.add_product(product, stockinfo)
    return basket


def create_order(number=None, basket=None, user=None, shipping_address=None,
                 shipping_method=None, billing_address=None,
                 total_incl_tax=None, total_excl_tax=None, **kwargs):
    """
    Helper method for creating an order for testing
    """
    if not basket:
        basket = Basket.objects.create()
        product = create_product()
        record = create_stockrecord(
            product, num_in_stock=10, price_excl_tax=D('10.00'))
        info = create_stockinfo(record)
        basket.add_product(product, info)
    if not basket.id:
        basket.save()
    if shipping_method is None:
        shipping_method = Free()
    if total_incl_tax is None or total_excl_tax is None:
        calc = OrderTotalCalculator()
        total_incl_tax = calc.order_total_incl_tax(basket, shipping_method)
        total_excl_tax = calc.order_total_excl_tax(basket, shipping_method)
    order = OrderCreator().place_order(
            order_number=number,
            user=user,
            basket=basket,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            billing_address=billing_address,
            total_incl_tax=total_incl_tax,
            total_excl_tax=total_excl_tax,
            **kwargs)
    basket.set_as_submitted()
    return order


def create_offer(name="Dummy offer", offer_type="Site",
                 max_basket_applications=None, range=None, condition=None,
                 benefit=None):
    """
    Helper method for creating an offer
    """
    if range is None:
        range = Range.objects.create(name="All products range",
                                    includes_all_products=True)
    if condition is None:
        condition = Condition.objects.create(
            range=range, type=Condition.COUNT, value=1)
    if benefit is None:
        benefit = Benefit.objects.create(
            range=range, type=Benefit.PERCENTAGE, value=20)
    return ConditionalOffer.objects.create(
        name=name,
        offer_type=offer_type,
        condition=condition,
        benefit=benefit,
        max_basket_applications=max_basket_applications)


def create_voucher():
    """
    Helper method for creating a voucher
    """
    voucher = Voucher.objects.create(
        name="Test voucher",
        code="test",
        start_date=datetime.date.today(),
        end_date=datetime.date.today() + datetime.timedelta(days=12))
    voucher.offers.add(create_offer(offer_type='Voucher'))
    return voucher
