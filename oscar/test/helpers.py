from decimal import Decimal as D
import random
import datetime

from oscar.apps.basket.models import Basket
from oscar.apps.catalogue.models import ProductClass, Product, ProductAttribute, ProductAttributeValue
from oscar.apps.checkout.calculators import OrderTotalCalculator
from oscar.apps.order.utils import OrderCreator
from oscar.apps.partner.models import Partner, StockRecord
from oscar.apps.shipping.methods import Free
from oscar.apps.offer.models import Range, ConditionalOffer, Condition, Benefit
from oscar.apps.voucher.models import Voucher


def create_product(price=None, title="Dummy title", product_class="Dummy item class", 
        partner="Dummy partner", partner_sku=None, upc=None, num_in_stock=10, attributes=None):
    """
    Helper method for creating products that are used in tests.
    """
    ic,_ = ProductClass._default_manager.get_or_create(name=product_class)
    item = Product._default_manager.create(title=title, product_class=ic, upc=upc)
    if price is not None or partner_sku or num_in_stock is not None:
        if not partner_sku:
            partner_sku = 'sku_%d_%d' % (item.id, random.randint(0, 10000))
        if not price:
            price = D('10.00')

        partner,_ = Partner._default_manager.get_or_create(name=partner)
        StockRecord._default_manager.create(product=item, partner=partner,
                                            partner_sku=partner_sku,
                                            price_excl_tax=price, num_in_stock=num_in_stock)
    if attributes:
        for key, value in attributes.items():
            attr,_ = ProductAttribute.objects.get_or_create(name=key, code=key)
            ProductAttributeValue.objects.create(product=item, attribute=attr, value=value)

    return item


def create_order(number=None, basket=None, user=None, shipping_address=None, shipping_method=None,
        billing_address=None, total_incl_tax=None, total_excl_tax=None, **kwargs):
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
            **kwargs
            )
    return order


def create_offer():
    """
    Helper method for creating an offer
    """
    range = Range.objects.create(name="All products range", includes_all_products=True)
    condition = Condition.objects.create(range=range,
                                         type=Condition.COUNT,
                                         value=1)
    benefit = Benefit.objects.create(range=range,
                                     type=Benefit.PERCENTAGE,
                                     value=20)
    offer = ConditionalOffer.objects.create(
        name='Dummy offer',
        offer_type='Site',
        condition=condition,
        benefit=benefit
    )
    return offer


def create_voucher():
    """
    Helper method for creating a voucher
    """
    voucher = Voucher.objects.create(
        name="Test voucher",
        code="test",
        start_date=datetime.date.today(),
        end_date=datetime.date.today() + datetime.timedelta(days=12)
    )
    voucher.offers.add(create_offer())
    return voucher
