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
