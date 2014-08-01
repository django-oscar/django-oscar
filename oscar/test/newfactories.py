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

from django.utils.timezone import now
import factory

from oscar.core.loading import get_model, get_class
from oscar.core.compat import get_user_model

__all__ = ["UserFactory", "CountryFactory", "UserAddressFactory",
           "BasketFactory", "VoucherFactory", "ProductFactory",
           "ProductClassFactory", "StockRecordFactory",
           "ProductAttributeFactory", "ProductAttributeValueFactory",
           "AttributeOptionGroupFactory",
           "AttributeOptionFactory", "PartnerFactory",
           "ProductCategoryFactory", "CategoryFactory", "RangeFactory"]

Selector = get_class('partner.strategy', 'Selector')


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_user_model()

    username = factory.Sequence(lambda n: 'the_j_meister nummer %d' % n)
    email = factory.Sequence(lambda n: 'example_%s@example.com' % n)
    first_name = 'joseph'
    last_name = 'winterbottom'
    password = factory.PostGenerationMethodCall('set_password', 'skelebrain')
    is_active = True
    is_superuser = False
    is_staff = False


class CountryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('address', 'Country')

    iso_3166_1_a2 = 'GB'
    name = "UNITED KINGDOM"


class UserAddressFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('address', 'UserAddress')

    title = "Dr"
    first_name = "Barry"
    last_name = 'Barrington'
    line1 = "1 King Road"
    line4 = "London"
    postcode = "SW1 9RE"
    country = factory.SubFactory(CountryFactory)
    user = factory.SubFactory(UserFactory)


class BasketFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('basket', 'Basket')

    @factory.post_generation
    def set_strategy(self, create, extracted, **kwargs):
        # Load default strategy (without a user/request)
        self.strategy = Selector().strategy()


class VoucherFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('voucher', 'Voucher')

    name = "My voucher"
    code = "MYVOUCHER"

    start_datetime = now() - datetime.timedelta(days=1)
    end_datetime = now() - datetime.timedelta(days=10)


class PartnerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('partner', 'Partner')

    name = "Gardners"


class StockRecordFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('partner', 'StockRecord')

    partner = factory.SubFactory(PartnerFactory)
    partner_sku = factory.Sequence(lambda n: 'unit%d' % n)
    price_currency = "GBP"
    price_excl_tax = D('9.99')
    num_in_stock = 100


class ProductClassFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'ProductClass')

    name = "Books"
    requires_shipping = True
    track_stock = True


class CategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'Category')

    name = factory.Sequence(lambda n: 'Category %d' % n)

    # Very naive handling of treebeard node fields. Works though!
    depth = 0
    path = factory.Sequence(lambda n: '%04d' % n)


class ProductCategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'ProductCategory')

    category = factory.SubFactory(CategoryFactory)


class ProductFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'Product')

    structure = FACTORY_FOR.STANDALONE
    upc = factory.Sequence(lambda n: '978080213020%d' % n)
    title = "A confederacy of dunces"
    product_class = factory.SubFactory(ProductClassFactory)

    stockrecords = factory.RelatedFactory(StockRecordFactory, 'product')
    categories = factory.RelatedFactory(ProductCategoryFactory, 'product')


class ProductAttributeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'ProductAttribute')

    code = name = 'weight'
    product_class = factory.SubFactory(ProductClassFactory)
    type = "float"


class AttributeOptionGroupFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'AttributeOptionGroup')

    name = u'Grüppchen'


class AttributeOptionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'AttributeOption')

    # Ideally we'd get_or_create a AttributeOptionGroup here, but I'm not
    # aware of how to not create a unique option group for each call of the
    # factory

    option = factory.Sequence(lambda n: 'Option %d' % n)


class ProductAttributeValueFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('catalogue', 'ProductAttributeValue')

    attribute = factory.SubFactory(ProductAttributeFactory)
    product = factory.SubFactory(ProductFactory)


class RangeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = get_model('offer', 'Range')

    name = factory.Sequence(lambda n: 'Range %d' % n)
    slug = factory.Sequence(lambda n: 'range-%d' % n)
