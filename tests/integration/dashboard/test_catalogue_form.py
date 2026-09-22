from django.test import TestCase

from oscar.apps.dashboard.catalogue import forms
from oscar.test import factories


class TestCreateProductForm(TestCase):
    def setUp(self):
        self.product_class = factories.ProductClassFactory()

    def submit(self, data, parent=None):
        return forms.ProductForm(self.product_class, parent=parent, data=data)

    def test_validates_that_parent_products_must_have_title(self):
        form = self.submit({"structure": "parent"})
        self.assertFalse(form.is_valid())
        form = self.submit({"structure": "parent", "title": "foo"})
        self.assertTrue(form.is_valid())

    def test_validates_that_child_products_dont_need_a_title(self):
        parent = factories.ProductFactory(
            product_class=self.product_class, structure="parent"
        )
        form = self.submit({"structure": "child"}, parent=parent)
        self.assertTrue(form.is_valid())


class TestCreateProductAttributeForm(TestCase):
    def test_can_create_without_code(self):
        form = forms.ProductAttributesForm(data={"name": "Attr", "type": "text"})

        self.assertTrue(form.is_valid())

        product_attribute = form.save()

        # check that code is not None or empty string
        self.assertTrue(product_attribute.code)

    def test_option_group_required_if_attribute_is_option_or_multi_option(self):
        option_form = forms.ProductAttributesForm(
            data={"name": "Attr", "type": "option"}
        )
        self.assertFalse(option_form.is_valid())
        self.assertEqual(
            option_form.errors, {"option_group": ["An option group is required"]}
        )

        multi_option_form = forms.ProductAttributesForm(
            data={"name": "Attr", "type": "option"}
        )
        self.assertFalse(multi_option_form.is_valid())
        self.assertEqual(
            multi_option_form.errors, {"option_group": ["An option group is required"]}
        )


class TestProductFormOptionAttributes(TestCase):
    def setUp(self):
        self.product_class = factories.ProductClassFactory()

    def create_attribute(self, attribute_type, option_group=None):
        return factories.ProductAttributeFactory(
            product_class=self.product_class,
            code="size",
            name="Size",
            type=attribute_type,
            required=False,
            option_group=option_group,
        )

    def test_option_attribute_without_option_group_has_empty_choices(self):
        for attribute_type in ("option", "multi_option"):
            with self.subTest(attribute_type=attribute_type):
                self.product_class.attributes.all().delete()
                self.create_attribute(attribute_type)

                form = forms.ProductForm(self.product_class)

                self.assertIn("attr_size", form.fields)
                field = form.fields["attr_size"]
                self.assertEqual(list(field.queryset), [])
                self.assertTrue(field.help_text)

    def test_option_attribute_with_option_group_gets_a_field(self):
        for attribute_type in ("option", "multi_option"):
            with self.subTest(attribute_type=attribute_type):
                self.product_class.attributes.all().delete()
                group = factories.AttributeOptionGroupFactory()
                option = factories.AttributeOptionFactory(group=group)
                self.create_attribute(attribute_type, option_group=group)

                form = forms.ProductForm(self.product_class)

                self.assertIn("attr_size", form.fields)
                field = form.fields["attr_size"]
                self.assertEqual(list(field.queryset), [option])
                self.assertFalse(field.help_text)
