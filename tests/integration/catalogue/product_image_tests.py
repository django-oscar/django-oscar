from django.test import TestCase

from oscar.test import factories


class TestProductImages(TestCase):

    def setUp(self):
        self.product = factories.create_product()
        self.im_1 = factories.create_product_image(product=self.product,
                                                   display_order=0)
        self.im_2 = factories.create_product_image(product=self.product,
                                                   display_order=1)
        self.im_3 = factories.create_product_image(product=self.product,
                                                   display_order=2)
        self.im_4 = factories.create_product_image(product=self.product,
                                                   display_order=3)

    def test_images_are_in_consecutive_order(self):
        self.product.images.all()[2].delete()

        for idx, im in enumerate(self.product.images.all()):
            self.assertEqual(im.display_order, idx)
