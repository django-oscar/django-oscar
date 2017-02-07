# coding=utf-8
from django.db import IntegrityError
from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.catalogue.models import (Product, ProductClass,
                                         ProductAttribute,
                                         AttributeOption)
from oscar.test import factories


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


class ChildProductTests(ProductTests):

    def setUp(self):
        super(ChildProductTests, self).setUp()
        self.parent = Product.objects.create(
            title="Parent product",
            product_class=self.product_class,
            structure=Product.PARENT,
            is_discountable=False)

    def test_child_products_dont_need_titles(self):
        Product.objects.create(
            parent=self.parent, structure=Product.CHILD)

    def test_child_products_dont_need_a_product_class(self):
        Product.objects.create(parent=self.parent, structure=Product.CHILD)

    def test_child_products_inherit_fields(self):
        p = Product.objects.create(
            parent=self.parent,
            structure=Product.CHILD,
            is_discountable=True)
        self.assertEqual("Parent product", p.get_title())
        self.assertEqual("Clothing", p.get_product_class().name)
        self.assertEqual(False, p.get_is_discountable())

    def test_child_products_are_not_part_of_browsable_set(self):
        Product.objects.create(
            product_class=self.product_class, parent=self.parent,
            structure=Product.CHILD)
        self.assertEqual(set([self.parent]), set(Product.browsable.all()))


class TestAChildProduct(TestCase):

    def setUp(self):
        clothing = ProductClass.objects.create(
            name='Clothing', requires_shipping=True)
        self.parent = clothing.products.create(
            title="Parent", structure=Product.PARENT)
        self.child = self.parent.children.create(structure=Product.CHILD)

    def test_delegates_requires_shipping_logic(self):
        self.assertTrue(self.child.is_shipping_required)


class ProductAttributeCreationTests(TestCase):

    def test_validating_option_attribute(self):
        option_group = factories.AttributeOptionGroupFactory()
        option_1 = factories.AttributeOptionFactory(group=option_group)
        option_2 = factories.AttributeOptionFactory(group=option_group)
        pa = factories.ProductAttribute(
            type='option', option_group=option_group)

        self.assertRaises(ValidationError, pa.validate_value, 'invalid')
        pa.validate_value(option_1)
        pa.validate_value(option_2)

        invalid_option = AttributeOption(option='invalid option')
        self.assertRaises(
            ValidationError, pa.validate_value, invalid_option)

    def test_entity_attributes(self):
        unrelated_object = factories.PartnerFactory()
        attribute = factories.ProductAttributeFactory(type='entity')

        attribute_value = factories.ProductAttributeValueFactory(
            attribute=attribute, value_entity=unrelated_object)

        self.assertEqual(attribute_value.value, unrelated_object)
