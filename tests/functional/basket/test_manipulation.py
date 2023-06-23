from oscar.apps.basket import models
from oscar.core.loading import get_model
from oscar.test import factories
from oscar.test.testcases import WebTestCase

Option = get_model("catalogue", "Option")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")


class TestAddingToBasket(WebTestCase):
    def test_works_for_standalone_product(self):
        product = factories.ProductFactory()

        detail_page = self.get(product.get_absolute_url())
        response = detail_page.forms["add_to_basket_form"].submit()

        self.assertIsRedirect(response)
        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))

        basket = baskets[0]
        self.assertEqual(1, basket.num_items)

    def test_works_for_child_product(self):
        parent = factories.ProductFactory(structure="parent", stockrecords=[])
        for _ in range(3):
            variant = factories.ProductFactory(parent=parent, structure="child")

            detail_page = self.get(variant.get_absolute_url())
            form = detail_page.forms["add_to_basket_form"]
            response = form.submit()

            self.assertIsRedirect(response)

        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))

        basket = baskets[0]
        self.assertEqual(3, basket.num_items)

    def test_validation_errors_in_form(self):
        product = factories.ProductFactory()
        product_class = product.get_product_class()
        group = AttributeOptionGroup.objects.create(name="checkbox options")
        AttributeOption.objects.create(group=group, option="1")
        AttributeOption.objects.create(group=group, option="2")

        option = Option.objects.create(
            type=Option.CHECKBOX,
            required=True,
            name="Required checkbox",
            option_group=group,
        )
        text_option = Option.objects.create(
            type=Option.TEXT, required=False, name="Open tekst"
        )

        product_class.options.add(option)
        product_class.options.add(text_option)
        product_class.save()

        detail_page = self.get(product.get_absolute_url())
        detail_page.forms["add_to_basket_form"]["open-tekst"] = "test harrie"
        response = detail_page.forms["add_to_basket_form"].submit().follow()

        self.assertEqual(
            response.forms["add_to_basket_form"]["open-tekst"].value, "test harrie"
        )
        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))

        basket = baskets[0]
        self.assertEqual(0, basket.lines.count())
