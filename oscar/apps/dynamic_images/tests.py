from django.conf import settings
from django.utils import unittest
from oscar.apps.dynamic_images import ImageModifier
from oscar.apps.dynamic_images.exceptions import ResizerFormatException
from oscar.apps.dynamic_images.mods import AutotrimMod, CropMod, ResizeMod
import os
import Image

TEST_IMAGE = os.path.join(os.path.dirname(__file__), 'test_fixtures/test.jpg')

class ModifierTestCase(unittest.TestCase):

    def setUp(self):
        self.base_config = settings.DYNAMIC_MEDIA_CONFIG

    def tearDown(self):
        pass

    def test_process_path_nochange(self):
        path = '/path/to/image.jpg'
        modifier = ImageModifier(path,self.base_config)
        
        filename = modifier.source_filename
        params = modifier._params
        
        self.assertEquals(filename,'/path/to/image.jpg')
        self.assertEquals(params['type'],'jpg')
        
    def test_process_path_invalid_ext(self):
        path = '/path/to/image.ext'

        with self.assertRaises(ResizerFormatException):
            ImageModifier(path,self.base_config)
            
    def test_process_path_change_ext(self):
        path = '/path/to/image.jpg.to.gif'
        modifier = ImageModifier(path,self.base_config)
        
        filename = modifier.source_filename
        params = modifier._params
        
        self.assertEquals(filename,'/path/to/image.jpg')
        self.assertEquals(params['type'],'gif')
        
    def test_process_path_with_param(self):
        path = '/path/to/image.jpg.width-300.png'
        modifier = ImageModifier(path,self.base_config)
        
        filename = modifier.source_filename
        params = modifier._params
        
        self.assertEquals(filename, '/path/to/image.jpg')
        self.assertEquals(params['type'], 'png')
        self.assertEquals(params['width'], '300')
        self.assertEquals(len(params), 2)

    def test_process_path_with_params(self):
        path = '/path/to/image.jpg.width-300_height-200.png'
        modifier = ImageModifier(path,self.base_config)
        
        filename = modifier.source_filename
        params = modifier._params

        self.assertEquals(filename, '/path/to/image.jpg')
        self.assertEquals(params['type'], 'png')
        self.assertEquals(params['width'], '300')
        self.assertEquals(params['height'], '200')
        self.assertEquals(len(params), 3)
        
    def test_process_path_with_unusual_params(self):
        path = '/path/to/image.jpg.width-300_height-200_crop-400,40,1000,1000.png'
        modifier = ImageModifier(path,self.base_config)
        
        filename = modifier.source_filename
        params = modifier._params

        self.assertEquals(filename, '/path/to/image.jpg')
        self.assertEquals(params['type'], 'png')
        self.assertEquals(params['width'], '300')
        self.assertEquals(params['height'], '200')
        self.assertEquals(params['crop'], '400,40,1000,1000')
        self.assertEquals(len(params), 4)        
        
    def test_process_path_unusual_nochange_filenames(self):
        test_filenames = (
            '/path/to/image.jpg..png',
            '/path/to/image.jpg.png',
            '/path/to/image.jpg._.png',
        )
        
        for t in test_filenames:
            modifier = ImageModifier(t, self.base_config)
            filename = modifier.source_filename
            self.assertEquals(filename, t)         
            
    def test_process_path_dots_in_path(self):
        path = '/path.to/image.jpg.width-300_height-200.png'
        modifier = ImageModifier(path, self.base_config)
        
        filename = modifier.source_filename
        
        self.assertEquals(filename, '/path.to/image.jpg')
        
        path = '/path.to/another.nice/image.jpg.width-300_height-200.png'
        modifier = ImageModifier(path, self.base_config)
        
        filename = modifier.source_filename
        
        self.assertEquals(filename, '/path.to/another.nice/image.jpg')
        
    def test_process_path_dots_in_filename(self):
        path = '/path.to/image.ext.jpg.width-300_height-200.png'
        modifier = ImageModifier(path, self.base_config)
        
        filename = modifier.source_filename
        
        self.assertEquals(filename, '/path.to/image.ext.jpg')


class ImageModTestCase(unittest.TestCase):

    def setUp(self):
        self.image = Image.open(TEST_IMAGE)

    def tearDown(self):
        pass
    
    def test_correct_image(self):
        """ Sanity check to make sure it's the right test image """
        self.assertEquals(self.image.size, (1535, 1800))
        
    def test_resize(self):
        mod = ResizeMod(self.image, dict(width=200, height=200))
        im = mod.apply()
        
        self.assertEquals(im.size, (200, 200))
        self.assertEquals(self.image.size, (1535, 1800))  # Mod shouldn't change original
        
    def test_resize_rounding(self):
        mod = ResizeMod(self.image, dict(width=200))
        im = mod.apply()        
        
        self.assertEquals(im.size, (200, 235)) # Check scaling rounds up
        
        mod = ResizeMod(self.image, dict(height=200))
        im = mod.apply()
        
        self.assertEquals(im.size, (171, 200))
        
    def test_crop(self):
        mod = CropMod(self.image, dict(crop='50,25,200,200'))
        im = mod.apply()
        
        self.assertEquals(im.size, (150, 175))
        self.assertEquals(self.image.size, (1535, 1800))  # Mod shouldn't change original