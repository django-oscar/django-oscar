from decimal import Decimal as D
import random
import datetime

from django.db.models import get_model

from oscar.core.loading import get_class
from oscar.apps.offer import models

Basket = get_model('basket', 'Basket')
Free = get_class('shipping.methods', 'Free')
Voucher = get_model('voucher', 'Voucher')
OrderCreator = get_class('order.utils', 'OrderCreator')
OrderTotalCalculator = get_class('checkout.calculators',
                                 'OrderTotalCalculator')
Partner = get_model('partner', 'Partner')
StockRecord = get_model('partner', 'StockRecord')

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')


def create_product(price=None, title=u"Dummy title",
                   product_class=u"Dummy item class",
                   partner=u"Dummy partner", partner_sku=None, upc=None,
                   num_in_stock=10, attributes=None, **kwargs):
    """
    Helper method for creating products that are used in tests.
    """
    ic, __ = ProductClass._default_manager.get_or_create(name=product_class)
    item = Product(title=title, product_class=ic, upc=upc, **kwargs)

    if attributes:
        for key, value in attributes.items():
            # Ensure product attribute exists
            ProductAttribute.objects.get_or_create(
                name=key, code=key, product_class=ic)
            setattr(item.attr, key, value)

    item.save()

    if price is not None or partner_sku or num_in_stock is not None:
        if not partner_sku:
            partner_sku = 'sku_%d_%d' % (item.id, random.randint(0, 10000))
        if price is None:
            price = D('10.00')

        partner, __ = Partner._default_manager.get_or_create(name=partner)
        StockRecord._default_manager.create(
            product=item, partner=partner, partner_sku=partner_sku,
            price_excl_tax=price, num_in_stock=num_in_stock)
    return item


def create_order(number=None, basket=None, user=None, shipping_address=None,
                 shipping_method=None, billing_address=None,
                 total_incl_tax=None, total_excl_tax=None, **kwargs):
    """
    Helper method for creating an order for testing
    """
    if not basket:
        basket = Basket.objects.create()
        basket.add_product(create_product(price=D('10.00')))
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
        range = models.Range.objects.create(name="All products range",
                                            includes_all_products=True)
    if condition is None:
        condition = models.Condition.objects.create(
            range=range, type=models.Condition.COUNT, value=1)
    if benefit is None:
        benefit = models.Benefit.objects.create(
            range=range, type=models.Benefit.PERCENTAGE, value=20)
    return models.ConditionalOffer.objects.create(
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
