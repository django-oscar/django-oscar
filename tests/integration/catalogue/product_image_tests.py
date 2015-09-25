from django.test import TestCase

from oscar.test import factories


class TestProductImages(TestCase):

    def test_images_are_in_consecutive_order(self):
        product = factories.StandaloneProductFactory()
        for display_order in range(4):
            factories.create_product_image(product=product, display_order=display_order)

        product.images.all()[2].delete()

        for idx, im in enumerate(product.images.all()):
            self.assertEqual(im.display_order, idx)
