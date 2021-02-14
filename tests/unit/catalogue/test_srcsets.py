import unittest
import oscar.utils.srcsets as srcsets
from unittest.mock import Mock
from django.test import TestCase
from oscar.apps.catalogue.models import Product, ProductImage
from django.core.files.storage import get_storage_class

def get_mocks():
    product = Product(
        title='utTestProduct_1',
        slug='ut-Test-Product-1'
    )
    image_1 = ProductImage(
        original='test/test_img.png',
        caption='test image 1',
        product=product,
    )
    settings = Mock()
    settings.SRCSETS = {
        'fullsizes': {
            'fullscreen': 1080,
            'tablet': 780,
            'mobile_large': 520,
            'moble_small': 280,
        },
        'thumbnails': {
            'large': 100,
            'small': 50,
        }
    }
    return product, image_1, settings

class test_functions(TestCase):

    def setUpClass(cls):
        #copy test image to sites media storage
        storage = get_storage_class()
        return
    def tearDownClass(cls):
        # remove test images from sites media storage
        # if it wasn't removed by the tests.
        storage = get_storage_class()
        return

    def test__get_srcset_sizes(self):
        product, image_1, settings = get_mocks()
        actual = srcsets._get_srcset_sizes(settings.SRCSETS, image_type='fullsizes')
        self.assertListEqual(list(actual), [
            ('fullsizes','fullscreen',1080),
            ('fullsizes','tablet',780),
            ('fullsizes','mobile_large',520),
            ('fullsizes','moble_small',280)
        ], 'Test_1')
        actual = srcsets._get_srcset_sizes(settings.SRCSETS, image_type='thumbnails')
        self.assertListEqual(list(actual), [
            ('thumbnails','large',100),
            ('thumbnails','small',50)
        ], 'Test_2')
        actual = srcsets._get_srcset_sizes(settings.SRCSETS, image_type=None)
        self.assertListEqual(list(actual), [
            ('fullsizes','fullscreen',1080),
            ('fullsizes','tablet',780),
            ('fullsizes','mobile_large',520),
            ('fullsizes','moble_small',280),
            ('thumbnails','large',100),
            ('thumbnails','small',50)
        ], 'Test_3')
        actual = srcsets._get_srcset_sizes(settings.SRCSETS, image_type='non_existant_image_type')
        self.assertListEqual(list(actual), [], 'Test_4')
        return
    def test_get_srcset_image(self):
        product, image_1, settings = get_mocks()

        # note that the image I'm testing with 644px wide to start so with upscale turned off
        # there should be two values not scaled for. 
        actual = srcsets.get_srcset_image(image_1.original, 520, image_processor=None, do_upscale=False,
            settings=settings)
        self.assertAlmostEqual(actual.width, 520, delta=5, msg=f"Test_1")

        #test upscaling:
        actual = srcsets.get_srcset_image(image_1.original, 1080, image_processor=None, do_upscale=False,
            settings=settings)
        self.assertIsNone(actual, f"Test_2a")
        actual = srcsets.get_srcset_image(image_1.original, 1080, image_processor=None, do_upscale=True,
            settings=settings)
        self.assertEqual(actual.width, 1080, 'Test_2b')

        #test image_proccessor passed in
        mock_image_processor = Mock()
        mock_image_processor.return_value = 1
        actual = srcsets.get_srcset_image(image_1.original, 520, image_processor=mock_image_processor, do_upscale=False,
            settings=settings)
        self.assertEqual(actual, 1)
        return
    def test_get_srcset(self):
        product, image_1, settings = get_mocks()

        # note that the image I'm testing with 833px wide to start so with upscale turned off
        # there should be two values not scaled for. 
        actual = srcsets.get_srcset(image_1.original, image_processor=None, do_upscale=False,
            settings=settings)
        actual = list(actual)
        self.assertEqual(len(actual), 4)
        self.assertAlmostEqual(actual[0].width, 520, delta=5, msg=f"Test_1")
        self.assertAlmostEqual(actual[1].width, 280, delta=5, msg=f"Test_2")
        self.assertAlmostEqual(actual[2].width, 100, delta=5, msg=f"Test_3")
        self.assertAlmostEqual(actual[3].width, 50, delta=5, msg=f"Test_4")

        return

    def test_collection(self):
        product, image_1, settings = get_mocks()
        collection = image_1.srcset

        self.assertEqual(collection.mobile_large.width, 520, 'Test_2')
        self.assertEqual(len(collection.fullsizes),2, 'Test_2')
        self.assertEqual(len(collection.thumbnails),2, 'Test_3')
        self.assertEqual(len(collection),4, 'Test_4')
        self.assertEqual(collection[520].width, 520, 'Test_5')
        self.assertEqual(collection['mobile_large'].width, 520, 'Test_6')
        with self.assertRaises(AttributeError, msg='Test_7'):
            collection.attr_does_not_exist
