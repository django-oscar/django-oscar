# coding=utf-8
import factory

from oscar.core.loading import get_model

__all__ = [
    'ProductClassFactory', 'ProductFactory',
    'CategoryFactory', 'ProductCategoryFactory',
    'ProductAttributeFactory', 'AttributeOptionGroupFactory',
    'OptionFactory', 'AttributeOptionFactory',
    'ProductAttributeValueFactory', 'ProductReviewFactory',
    'ProductImageFactory'
]


class ProductClassFactory(factory.django.DjangoModelFactory):
    name = "Books"
    requires_shipping = True
    track_stock = True

    class Meta:
        model = get_model('catalogue', 'ProductClass')


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('catalogue', 'Product')

    structure = Meta.model.STANDALONE
    upc = factory.Sequence(lambda n: '978080213020%d' % n)
    title = "A confederacy of dunces"
    product_class = factory.SubFactory(ProductClassFactory)

    stockrecords = factory.RelatedFactory(
        'oscar.test.factories.StockRecordFactory', 'product')
    categories = factory.RelatedFactory(
        'oscar.test.factories.ProductCategoryFactory', 'product')


class CategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Category %d' % n)

    # Very naive handling of treebeard node fields. Works though!
    depth = 1
    path = factory.Sequence(lambda n: '%04d' % n)

    class Meta:
        model = get_model('catalogue', 'Category')


class ProductCategoryFactory(factory.django.DjangoModelFactory):
    category = factory.SubFactory(CategoryFactory)

    class Meta:
        model = get_model('catalogue', 'ProductCategory')


class ProductAttributeFactory(factory.django.DjangoModelFactory):
    code = name = 'weight'
    product_class = factory.SubFactory(ProductClassFactory)
    type = "float"

    class Meta:
        model = get_model('catalogue', 'ProductAttribute')


class OptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('catalogue', 'Option')

    name = 'example option'
    code = 'example'
    type = Meta.model.TEXT
    required = False


class AttributeOptionFactory(factory.django.DjangoModelFactory):
    # Ideally we'd get_or_create a AttributeOptionGroup here, but I'm not
    # aware of how to not create a unique option group for each call of the
    # factory

    option = factory.Sequence(lambda n: 'Option %d' % n)

    class Meta:
        model = get_model('catalogue', 'AttributeOption')


class AttributeOptionGroupFactory(factory.django.DjangoModelFactory):
    name = 'Grüppchen'

    class Meta:
        model = get_model('catalogue', 'AttributeOptionGroup')


class ProductAttributeValueFactory(factory.django.DjangoModelFactory):
    attribute = factory.SubFactory(ProductAttributeFactory)
    product = factory.SubFactory(ProductFactory)

    class Meta:
        model = get_model('catalogue', 'ProductAttributeValue')


class ProductReviewFactory(factory.django.DjangoModelFactory):
    score = 5
    product = factory.SubFactory(ProductFactory, stockrecords=[])

    class Meta:
        model = get_model('reviews', 'ProductReview')


class ProductImageFactory(factory.django.DjangoModelFactory):
    product = factory.SubFactory(ProductFactory, stockrecords=[])
    original = factory.django.ImageField(width=100, height=200, filename='test_image.jpg')

    class Meta:
        model = get_model('catalogue', 'ProductImage')
