from oscar.test.testcases import WebTestCase
from oscar.test import factories
from oscar.apps.basket import models


class TestAddingToBasket(WebTestCase):

    def test_works_for_standalone_product(self):
        product = factories.ProductFactory()

        detail_page = self.get(product.get_absolute_url())
        response = detail_page.forms['add_to_basket_form'].submit()

        self.assertIsRedirect(response)
        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))

        basket = baskets[0]
        self.assertEqual(1, basket.num_items)

    def test_works_for_child_product(self):
        parent = factories.ProductFactory(structure='parent', stockrecords=[])
        for x in range(3):
            factories.ProductFactory(parent=parent, structure='child')

        detail_page = self.get(parent.get_absolute_url())
        form = detail_page.forms['add_to_basket_form']
        response = form.submit()

        self.assertIsRedirect(response)
        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))

        basket = baskets[0]
        self.assertEqual(1, basket.num_items)
        
    def test_works_with_attribute_option(self):
        option = factories.OptionFactory()
        product = factories.ProductFactory()
        product.product_options.add(option)
        detail_page = self.get(product.get_absolute_url())
        form = detail_page.forms['add_to_basket_form']
        form['weight'] = 12.0
        response = form.submit()
        self.assertIsRedirect(response)
        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))
        basket = baskets[0]
        lines = basket.lines.all()
        self.assertEqual(1, len(lines))
        line = lines[0]
        attributes = line.attributes.all()
        self.assertEqual(1, len(attributes))
        attribute = attributes[0]
        self.assertEqual(option, attribute.option)
        self.assertEqual(12.0, attribute.value)
        
    def test_cant_add_to_basket_without_required_option(self):
        option = factories.OptionFactory(name="message", type="text", required=True)
        product = factories.ProductFactory()
        product.product_options.add(option)
        detail_page = self.get(product.get_absolute_url())
        response = detail_page.forms['add_to_basket_form'].submit()
        self.assertEqual('302 FOUND', response.status)
        self.assertIn("This field is required", response.headers['Set-Cookie'])


