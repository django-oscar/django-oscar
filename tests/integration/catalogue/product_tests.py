# coding=utf-8
from django.db import IntegrityError
from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.catalogue.models import (Product, ProductClass,
                                         ProductAttribute,
                                         AttributeOptionGroup,
                                         AttributeOption)


class ProductTests(TestCase):

    def setUp(self):
        self.product_class, _ = ProductClass.objects.get_or_create(
            name='Clothing')


class ProductCreationTests(ProductTests):

    def setUp(self):
        super(ProductCreationTests, self).setUp()
        ProductAttribute.objects.create(product_class=self.product_class,
                                        name='Number of pages',
                                        code='num_pages',
                                        type='integer')
        Product.ENABLE_ATTRIBUTE_BINDING = True

    def tearDown(self):
        Product.ENABLE_ATTRIBUTE_BINDING = False

    def test_create_products_with_attributes(self):
        product = Product(upc='1234',
                          product_class=self.product_class,
                          title='testing')
        product.attr.num_pages = 100
        product.save()

    def test_none_upc_is_represented_as_empty_string(self):
        product = Product(product_class=self.product_class,
                          title='testing', upc=None)
        self.assertEqual(product.upc, u'')

    def test_upc_uniqueness_enforced(self):
        Product.objects.create(product_class=self.product_class,
                               title='testing', upc='bah')
        self.assertRaises(IntegrityError, Product.objects.create,
                          product_class=self.product_class,
                          title='testing', upc='bah')

    def test_allow_two_products_without_upc(self):
        for x in range(2):
            Product.objects.create(product_class=self.product_class,
                                   title='testing', upc=None)


class TopLevelProductTests(ProductTests):

    def test_top_level_products_must_have_titles(self):
        product = Product(product_class=self.product_class)
        self.assertRaises(ValidationError, product.clean)

    def test_top_level_products_must_have_product_class(self):
        product = Product(title=u"Kopfhörer")
        self.assertRaises(ValidationError, product.clean)

    def test_top_level_products_are_part_of_browsable_set(self):
        product = Product.objects.create(
            product_class=self.product_class, title=u"Kopfhörer")
        self.assertEqual(set([product]), set(Product.browsable.all()))


class VariantProductTests(ProductTests):

    def setUp(self):
        super(VariantProductTests, self).setUp()
        self.parent = Product.objects.create(
            title="Parent product", product_class=self.product_class)

    def test_variant_products_dont_need_titles(self):
        Product.objects.create(parent=self.parent, product_class=self.product_class)

    def test_variant_products_dont_need_a_product_class(self):
        Product.objects.create(parent=self.parent)

    def test_variant_products_inherit_parent_titles(self):
        p = Product.objects.create(parent=self.parent, product_class=self.product_class)
        self.assertEqual("Parent product", p.get_title())

    def test_variant_products_inherit_product_class(self):
        p = Product.objects.create(parent=self.parent)
        self.assertEqual("Clothing", p.get_product_class().name)

    def test_variant_products_are_not_part_of_browsable_set(self):
        Product.objects.create(
            product_class=self.product_class, parent=self.parent)
        self.assertEqual(set([self.parent]), set(Product.browsable.all()))


class TestAVariant(TestCase):

    def setUp(self):
        clothing = ProductClass.objects.create(
            name='Clothing', requires_shipping=True)
        self.parent = clothing.products.create(
            title="Parent")
        self.variant = self.parent.variants.create()

    def test_delegates_requires_shipping_logic(self):
        self.assertTrue(self.variant.is_shipping_required)


class ProductAttributeCreationTests(TestCase):

    def setUp(self):
        self.product_class,_ = ProductClass.objects.get_or_create(
            name='Clothing'
        )
        self.option_group = AttributeOptionGroup.objects.create(name='group')
        self.option_1 = AttributeOption.objects.create(group=self.option_group, option='first')
        self.option_2 = AttributeOption.objects.create(group=self.option_group, option='second')

    def test_validating_option_attribute(self):
        pa = ProductAttribute.objects.create(product_class=self.product_class,
                                             name='test group',
                                             code='test_group',
                                             type='option',
                                             option_group=self.option_group)

        self.assertRaises(ValidationError, pa.get_validator(), 'invalid')

        try:
            pa.get_validator()(self.option_1)
        except ValidationError:
            self.fail("valid option '%s' not validated" % self.option_1)

        try:
            pa.get_validator()(self.option_2)
        except ValidationError:
            self.fail("valid option '%s' not validated" % self.option_1)

        invalid_option = AttributeOption()
        invalid_option.option = 'invalid option'
        self.assertRaises(ValidationError, pa.get_validator(),
                          invalid_option)

