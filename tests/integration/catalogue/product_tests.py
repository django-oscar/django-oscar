from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.catalogue.models import (Product, ProductClass,
                                         ProductAttribute,
                                         AttributeOptionGroup,
                                         AttributeOption)


class ProductTests(TestCase):

    def setUp(self):
        self.product_class,_ = ProductClass.objects.get_or_create(name='Clothing')


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


class TopLevelProductTests(ProductTests):

    def test_top_level_products_must_have_titles(self):
        self.assertRaises(ValidationError, Product.objects.create, product_class=self.product_class)


class VariantProductTests(ProductTests):

    def setUp(self):
        super(VariantProductTests, self).setUp()
        self.parent = Product.objects.create(title="Parent product", product_class=self.product_class)

    def test_variant_products_dont_need_titles(self):
        Product.objects.create(parent=self.parent, product_class=self.product_class)

    def test_variant_products_dont_need_a_product_class(self):
        Product.objects.create(parent=self.parent)

    def test_variant_products_inherit_parent_titles(self):
        p = Product.objects.create(parent=self.parent, product_class=self.product_class)
        self.assertEquals("Parent product", p.get_title())

    def test_variant_products_inherit_product_class(self):
        p = Product.objects.create(parent=self.parent)
        self.assertEquals("Clothing", p.get_product_class().name)


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

