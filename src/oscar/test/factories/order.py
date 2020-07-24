from decimal import Decimal as D

import factory
from django.conf import settings

from oscar.core.loading import get_model
from oscar.core.utils import slugify
from oscar.test.factories.utils import tax_add, tax_subtract

__all__ = [
    'BillingAddressFactory', 'ShippingAddressFactory', 'OrderDiscountFactory',
    'OrderFactory', 'OrderLineFactory', 'ShippingEventTypeFactory',
    'ShippingEventFactory',
]


class BillingAddressFactory(factory.DjangoModelFactory):
    country = factory.SubFactory('oscar.test.factories.CountryFactory')

    first_name = 'John'
    last_name = 'Doe'
    line1 = 'Streetname'
    line2 = '1a'
    line4 = 'City'
    postcode = '1000AA'

    class Meta:
        model = get_model('order', 'BillingAddress')


class ShippingAddressFactory(factory.DjangoModelFactory):
    country = factory.SubFactory('oscar.test.factories.CountryFactory')

    first_name = 'John'
    last_name = 'Doe'
    line1 = 'Streetname'
    line2 = '1a'
    line4 = 'City'
    postcode = '1000 AA'
    phone_number = '+12125555555'

    class Meta:
        model = get_model('order', 'ShippingAddress')


class OrderDiscountFactory(factory.DjangoModelFactory):

    class Meta:
        model = get_model('order', 'OrderDiscount')


class OrderFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_model('order', 'Order')
        exclude = ('basket',)

    if hasattr(settings, 'OSCAR_INITIAL_ORDER_STATUS'):
        status = settings.OSCAR_INITIAL_ORDER_STATUS

    site_id = settings.SITE_ID
    number = factory.LazyAttribute(lambda o: '%d' % (100000 + o.basket.pk))
    basket = factory.SubFactory(
        'oscar.test.factories.BasketFactory')

    shipping_code = 'delivery'
    shipping_incl_tax = D('4.95')
    shipping_excl_tax = factory.LazyAttribute(
        lambda o: tax_subtract(o.shipping_incl_tax))

    total_incl_tax = factory.LazyAttribute(lambda o: o.basket.total_incl_tax)
    total_excl_tax = factory.LazyAttribute(lambda o: o.basket.total_excl_tax)

    guest_email = factory.LazyAttribute(
        lambda o: (
            '%s.%s@example.com' % (
                o.billing_address.first_name[0],
                o.billing_address.last_name
            )).lower())

    shipping_address = factory.SubFactory(ShippingAddressFactory)
    billing_address = factory.SubFactory(BillingAddressFactory)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        date_placed = kwargs.pop('date_placed', None)
        instance = super(OrderFactory, cls)._create(
            target_class, *args, **kwargs)

        if date_placed:
            instance.date_placed = date_placed
        return instance


class OrderLineFactory(factory.DjangoModelFactory):
    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(
        'oscar.test.factories.ProductFactory')
    partner_sku = factory.LazyAttribute(lambda l: l.product.upc)
    stockrecord = factory.LazyAttribute(
        lambda l: l.product.stockrecords.first())
    quantity = 1

    line_price_incl_tax = factory.LazyAttribute(lambda obj: tax_add(obj.stockrecord.price) * obj.quantity)
    line_price_excl_tax = factory.LazyAttribute(lambda obj: obj.stockrecord.price * obj.quantity)

    line_price_before_discounts_incl_tax = (
        factory.SelfAttribute('.line_price_incl_tax'))
    line_price_before_discounts_excl_tax = (
        factory.SelfAttribute('.line_price_excl_tax'))

    unit_price_incl_tax = factory.LazyAttribute(lambda obj: tax_add(obj.stockrecord.price))
    unit_price_excl_tax = factory.LazyAttribute(lambda obj: obj.stockrecord.price)

    class Meta:
        model = get_model('order', 'Line')


class ShippingEventTypeFactory(factory.DjangoModelFactory):
    name = 'Test event'
    code = factory.LazyAttribute(lambda o: slugify(o.name).replace('-', '_'))

    class Meta:
        model = get_model('order', 'ShippingEventType')
        django_get_or_create = ('code', )


class ShippingEventFactory(factory.DjangoModelFactory):

    order = factory.SubFactory(OrderFactory)
    event_type = factory.SubFactory(ShippingEventTypeFactory)

    class Meta:
        model = get_model('order', 'ShippingEvent')
