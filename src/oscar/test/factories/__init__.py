# coding=utf-8
from decimal import Decimal as D
import random
import datetime

from django.conf import settings
from django.utils import timezone

from oscar.apps.offer import models as range_models
from oscar.core.loading import get_class, get_model
from oscar.test.factories.address import *  # noqa
from oscar.test.factories.basket import *  # noqa
from oscar.test.factories.catalogue import *  # noqa
from oscar.test.factories.contrib import *  # noqa
from oscar.test.factories.customer import *  # noqa
from oscar.test.factories.models import *  # noqa
from oscar.test.factories.offer import *  # noqa
from oscar.test.factories.order import *  # noqa
from oscar.test.factories.partner import *  # noqa
from oscar.test.factories.payment import *  # noqa
from oscar.test.factories.voucher import *  # noqa
from oscar.test.factories.wishlists import *  # noqa


Basket = get_model('basket', 'Basket')
Free = get_class('shipping.methods', 'Free')
Voucher = get_model('voucher', 'Voucher')
OrderCreator = get_class('order.utils', 'OrderCreator')
OrderTotalCalculator = get_class('checkout.calculators',
                                 'OrderTotalCalculator')
Partner = get_model('partner', 'Partner')
StockRecord = get_model('partner', 'StockRecord')
PurchaseInfo = get_class('partner.strategy', 'PurchaseInfo')
Default = get_class('partner.strategy', 'Default')
StockRequired = get_class('partner.availability', 'StockRequired')
FixedPrice = get_class('partner.prices', 'FixedPrice')

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
ProductImage = get_model('catalogue', 'ProductImage')
ConditionalOffer = get_model('offer', 'ConditionalOffer')

WeightBand = get_model('shipping', 'WeightBand')
WeightBased = get_model('shipping', 'WeightBased')


def create_stockrecord(product=None, price_excl_tax=None, partner_sku=None,
                       num_in_stock=None, partner_name=None,
                       currency=settings.OSCAR_DEFAULT_CURRENCY,
                       partner_users=None):
    if product is None:
        product = create_product()
    partner, __ = Partner.objects.get_or_create(name=partner_name or '')
    if partner_users:
        for user in partner_users:
            partner.users.add(user)
    if price_excl_tax is None:
        price_excl_tax = D('9.99')
    if partner_sku is None:
        partner_sku = 'sku_%d_%d' % (product.id, random.randint(0, 10000))
    return product.stockrecords.create(
        partner=partner, partner_sku=partner_sku,
        price_currency=currency,
        price_excl_tax=price_excl_tax, num_in_stock=num_in_stock)


def create_purchase_info(record):
    return PurchaseInfo(
        price=FixedPrice(
            record.price_currency,
            record.price_excl_tax,
            D('0.00')  # Default to no tax
        ),
        availability=StockRequired(
            record.net_stock_level),
        stockrecord=record
    )


def create_product(upc=None, title=u"Dùｍϻϒ title",
                   product_class=u"Dùｍϻϒ item class",
                   partner_name=None, partner_sku=None, price=None,
                   num_in_stock=None, attributes=None,
                   partner_users=None, **kwargs):
    """
    Helper method for creating products that are used in tests.
    """
    product_class, __ = ProductClass._default_manager.get_or_create(
        name=product_class)
    product = product_class.products.model(
        product_class=product_class,
        title=title, upc=upc, **kwargs)
    if kwargs.get('parent') and 'structure' not in kwargs:
        product.structure = 'child'
    if attributes:
        for code, value in attributes.items():
            # Ensure product attribute exists
            product_class.attributes.get_or_create(name=code, code=code)
            setattr(product.attr, code, value)
    product.save()

    # Shortcut for creating stockrecord
    stockrecord_fields = [
        price, partner_sku, partner_name, num_in_stock, partner_users]
    if any([field is not None for field in stockrecord_fields]):
        create_stockrecord(
            product, price_excl_tax=price, num_in_stock=num_in_stock,
            partner_users=partner_users, partner_sku=partner_sku,
            partner_name=partner_name)
    return product


def create_product_image(product=None,
                         original=None,
                         caption='Dummy Caption',
                         display_order=None,
                         ):
    if not product:
        product = create_product()
    if not display_order:
        if not product.images.all():
            display_order = 0
        else:
            display_order = max(
                [i.display_order for i in product.images.all()]) + 1

    kwargs = {'product_id': product.id,
              'original': original,
              'display_order': display_order,
              'caption': caption, }

    return ProductImage.objects.create(**kwargs)


def create_basket(empty=False):
    basket = Basket.objects.create()
    basket.strategy = Default()
    if not empty:
        product = create_product()
        create_stockrecord(product, num_in_stock=2)
        basket.add_product(product)
    return basket


def create_order(number=None, basket=None, user=None, shipping_address=None,
                 shipping_method=None, billing_address=None,
                 total=None, **kwargs):
    """
    Helper method for creating an order for testing
    """
    if not basket:
        basket = Basket.objects.create()
        basket.strategy = Default()
        product = create_product()
        create_stockrecord(
            product, num_in_stock=10, price_excl_tax=D('10.00'))
        basket.add_product(product)
    if not basket.id:
        basket.save()
    if shipping_method is None:
        shipping_method = Free()
    shipping_charge = shipping_method.calculate(basket)
    if total is None:
        total = OrderTotalCalculator().calculate(basket, shipping_charge)
    order = OrderCreator().place_order(
        order_number=number,
        user=user,
        basket=basket,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        shipping_charge=shipping_charge,
        billing_address=billing_address,
        total=total,
        **kwargs)
    basket.set_as_submitted()
    return order


def create_offer(name=u"Dùｍϻϒ offer", offer_type="Site",
                 max_basket_applications=None, range=None, condition=None,
                 benefit=None, priority=0, status=None, start=None, end=None):
    """
    Helper method for creating an offer
    """
    if range is None:
        range, __ = range_models.Range.objects.get_or_create(
            name=u"All products räñgë", includes_all_products=True)
    if condition is None:
        condition, __ = range_models.Condition.objects.get_or_create(
            range=range, type=range_models.Condition.COUNT, value=1)
    if benefit is None:
        benefit, __ = range_models.Benefit.objects.get_or_create(
            range=range, type=range_models.Benefit.PERCENTAGE, value=20)
    if status is None:
        status = ConditionalOffer.OPEN

    # Create start and end date so offer is active
    now = timezone.now()
    if start is None:
        start = now - datetime.timedelta(days=1)
    if end is None:
        end = now + datetime.timedelta(days=30)

    return ConditionalOffer.objects.create(
        name=name,
        start_datetime=start,
        end_datetime=end,
        status=status,
        offer_type=offer_type,
        condition=condition,
        benefit=benefit,
        max_basket_applications=max_basket_applications,
        priority=priority)


def create_voucher(**kwargs):
    """
    Helper method for creating a voucher
    """
    defaults = {
        'name': u"Dùｍϻϒ voucher",
        'code': "test",
        'start_datetime': timezone.now(),
        'end_datetime': timezone.now() + datetime.timedelta(days=12)
    }
    defaults.update(kwargs)
    voucher = VoucherFactory(**defaults)
    voucher.offers.add(create_offer(offer_type='Voucher'))
    return voucher


def create_shipping_weight_based(default_weight=D(1)):
    return WeightBased.objects.create(
        default_weight=default_weight
    )


def create_shipping_weight_band(upper_limit, charge, weight_based=None):
    if not weight_based:
        weight_based = create_shipping_weight_based()
    return WeightBand.objects.create(
        method=weight_based,
        upper_limit=upper_limit,
        charge=charge
    )
