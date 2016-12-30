from django.test import TestCase

from oscar.test import factories


class TestProductImages(TestCase):

    def test_images_are_in_consecutive_order(self):
        product = factories.create_product()
        for i in range(4):
            factories.create_product_image(product=product, display_order=i)

        product.images.all()[2].delete()

        for idx, im in enumerate(product.images.all()):
            self.assertEqual(im.display_order, idx)
