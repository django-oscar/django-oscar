# coding=utf-8
"""
Factories using factory boy.

Using a silly module name as I don't want to mix the old and new
implementations of factories, but I do want to allow importing both from the
same place.

In 2020, when all tests use the new factory-boy factories, we can rename this
module to factories.py and drop the old ones.
"""
import datetime
from decimal import Decimal as D
from decimal import ROUND_HALF_UP

import factory
from django.conf import settings
from django.utils.timezone import now

from oscar.core.loading import get_model, get_class
from oscar.core.compat import get_user_model
from oscar.core.utils import slugify

__all__ = ["UserFactory", "CountryFactory", "UserAddressFactory",
           "BasketFactory", "VoucherFactory", "ProductFactory",
           "ProductClassFactory", "StockRecordFactory",
           "ProductAttributeFactory", "ProductAttributeValueFactory",
           "AttributeOptionGroupFactory",
           "AttributeOptionFactory", "PartnerFactory",
           "ProductCategoryFactory", "CategoryFactory", "RangeFactory",
           "ProductClassFactory"]

Selector = get_class('partner.strategy', 'Selector')


class UserFactory(factory.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'the_j_meister nummer %d' % n)
    email = factory.Sequence(lambda n: 'example_%s@example.com' % n)
    first_name = 'joseph'
    last_name = 'winterbottom'
    password = factory.PostGenerationMethodCall('set_password', 'skelebrain')
    is_active = True
    is_superuser = False
    is_staff = False

    class Meta:
        model = get_user_model()


class CountryFactory(factory.DjangoModelFactory):
    iso_3166_1_a2 = 'GB'
    name = "UNITED KINGDOM"

    class Meta:
        model = get_model('address', 'Country')
        django_get_or_create = ('iso_3166_1_a2',)



class UserAddressFactory(factory.DjangoModelFactory):
    title = "Dr"
    first_name = "Barry"
    last_name = 'Barrington'
    line1 = "1 King Road"
    line4 = "London"
    postcode = "SW1 9RE"
    country = factory.SubFactory(CountryFactory)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = get_model('address', 'UserAddress')


class BasketFactory(factory.DjangoModelFactory):
    @factory.post_generation
    def set_strategy(self, create, extracted, **kwargs):
        # Load default strategy (without a user/request)
        self.strategy = Selector().strategy()

    class Meta:
        model = get_model('basket', 'Basket')


class VoucherFactory(factory.DjangoModelFactory):
    name = "My voucher"
    code = "MYVOUCHER"

    start_datetime = now() - datetime.timedelta(days=1)
    end_datetime = now() - datetime.timedelta(days=10)

    class Meta:
        model = get_model('voucher', 'Voucher')


class PartnerFactory(factory.DjangoModelFactory):
    name = "Gardners"

    class Meta:
        model = get_model('partner', 'Partner')


class StockRecordFactory(factory.DjangoModelFactory):
    partner = factory.SubFactory(PartnerFactory)
    partner_sku = factory.Sequence(lambda n: 'unit%d' % n)
    price_currency = "GBP"
    price_excl_tax = D('9.99')
    num_in_stock = 100

    class Meta:
        model = get_model('partner', 'StockRecord')


class ProductClassFactory(factory.DjangoModelFactory):
    name = "Books"
    requires_shipping = True
    track_stock = True

    class Meta:
        model = get_model('catalogue', 'ProductClass')


class CategoryFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Category %d' % n)

    # Very naive handling of treebeard node fields. Works though!
    depth = 0
    path = factory.Sequence(lambda n: '%04d' % n)

    class Meta:
        model = get_model('catalogue', 'Category')


class ProductCategoryFactory(factory.DjangoModelFactory):
    category = factory.SubFactory(CategoryFactory)

    class Meta:
        model = get_model('catalogue', 'ProductCategory')


class ProductFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_model('catalogue', 'Product')

    structure = Meta.model.STANDALONE
    upc = factory.Sequence(lambda n: '978080213020%d' % n)
    title = "A confederacy of dunces"
    product_class = factory.SubFactory(ProductClassFactory)

    stockrecords = factory.RelatedFactory(StockRecordFactory, 'product')
    categories = factory.RelatedFactory(ProductCategoryFactory, 'product')


class ProductAttributeFactory(factory.DjangoModelFactory):
    code = name = 'weight'
    product_class = factory.SubFactory(ProductClassFactory)
    type = "float"

    class Meta:
        model = get_model('catalogue', 'ProductAttribute')


class AttributeOptionGroupFactory(factory.DjangoModelFactory):
    name = u'Grüppchen'

    class Meta:
        model = get_model('catalogue', 'AttributeOptionGroup')


class AttributeOptionFactory(factory.DjangoModelFactory):
    # Ideally we'd get_or_create a AttributeOptionGroup here, but I'm not
    # aware of how to not create a unique option group for each call of the
    # factory

    option = factory.Sequence(lambda n: 'Option %d' % n)

    class Meta:
        model = get_model('catalogue', 'AttributeOption')


class ProductAttributeValueFactory(factory.DjangoModelFactory):
    attribute = factory.SubFactory(ProductAttributeFactory)
    product = factory.SubFactory(ProductFactory)

    class Meta:
        model = get_model('catalogue', 'ProductAttributeValue')


class RangeFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Range %d' % n)
    slug = factory.Sequence(lambda n: 'range-%d' % n)

    class Meta:
        model = get_model('offer', 'Range')


class ShippingAddressFactory(factory.DjangoModelFactory):
    first_name = 'John'
    last_name = 'Doe'
    line1 = 'Streetname'
    line2 = '1a'
    line4 = 'City'
    postcode = '1000 AA'
    phone_number = '06-12345678'
    country = factory.SubFactory(CountryFactory)

    class Meta:
        model = get_model('order', 'ShippingAddress')


class BillingAddressFactory(factory.DjangoModelFactory):
    country = factory.SubFactory(CountryFactory)

    first_name = 'John'
    last_name = 'Doe'
    line1 = 'Streetname'
    line2 = '1a'
    line4 = 'City'
    postcode = '1000AA'

    class Meta:
        model = get_model('order', 'BillingAddress')


class OrderFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_model('order', 'Order')
        exclude = ('basket',)

    status = settings.OSCAR_INITIAL_ORDER_STATUS
    site_id = settings.SITE_ID
    number = factory.LazyAttribute(lambda o: '%d' % (100000 + o.basket.pk))
    basket = factory.SubFactory(BasketFactory)

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
    product = factory.SubFactory(ProductFactory)
    partner_sku = factory.LazyAttribute(lambda l: l.product.upc)
    stockrecord = factory.LazyAttribute(
        lambda l: l.product.stockrecords.first())
    quantity = 1

    line_price_incl_tax = factory.LazyAttribute(
        lambda obj: tax_add(obj.stockrecord.price_excl_tax) * obj.quantity)
    line_price_excl_tax = factory.LazyAttribute(
        lambda obj: obj.stockrecord.price_excl_tax * obj.quantity)

    line_price_before_discounts_incl_tax = (
        factory.SelfAttribute('.line_price_incl_tax'))
    line_price_before_discounts_excl_tax = (
        factory.SelfAttribute('.line_price_excl_tax'))

    unit_price_incl_tax = factory.LazyAttribute(
        lambda obj: tax_add(obj.stockrecord.price_excl_tax))
    unit_cost_price = factory.LazyAttribute(
        lambda obj: obj.stockrecord.cost_price)
    unit_price_excl_tax = factory.LazyAttribute(
        lambda obj: obj.stockrecord.price_excl_tax)
    unit_retail_price = factory.LazyAttribute(
        lambda obj: obj.stockrecord.price_retail)

    class Meta:
        model = get_model('order', 'Line')


class ShippingEventTypeFactory(factory.DjangoModelFactory):
    name = 'Test event'
    code =  factory.LazyAttribute(lambda o: slugify(o.name).replace('-', '_'))

    class Meta:
        model = get_model('order', 'ShippingEventType')
        django_get_or_create = ('code', )


class ShippingEventFactory(factory.DjangoModelFactory):

    order = factory.SubFactory(OrderFactory)
    event_type = factory.SubFactory(ShippingEventTypeFactory)

    class Meta:
        model = get_model('order', 'ShippingEvent')


def tax_subtract(price, tax_percentage=21):
    """Subtract the given `tax_percentage` from the given `price`."""
    if price is None:
        return None

    result = price / ((100 + tax_percentage) / D(100))
    return result.quantize(D('0.01'), ROUND_HALF_UP)


def tax_add(price, tax_percentage=21):
    """Add the given `tax_percentage` to the given `price`."""
    if price is None:
        return None

    result = price * ((100 + tax_percentage) / D(100))
    return result.quantize(D('0.01'), ROUND_HALF_UP)
