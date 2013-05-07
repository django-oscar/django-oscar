# -*- coding: utf-8 -*-
from django.test import TestCase

from oscar.apps.catalogue.models import Product, ProductClass, Category


class TestProductPickling(TestCase):
    def setUp(self):
        self.product_class, _ = ProductClass.objects.get_or_create(
            name='Pickle')

    def test_product_pickling_works(self):
        import pickle
        from StringIO import StringIO

        src = StringIO()
        pickler = pickle.Pickler(src)

        product = Product.objects.create(title='test_pickle_product',
                                         product_class=self.product_class)

        pickler.dump(product)

        dst = StringIO(src.getvalue())
        unpickler = pickle.Unpickler(dst)

        product_pickle = unpickler.load()

        pickler.dump(product_pickle)


class TestReceivingDeleteImageSignal(TestCase):

    def test_doesnt_fail_for_empty_image_field(self):
        category = Category.add_root(name='Test Category')
        from oscar.apps.catalogue.receivers import delete_image_files
        delete_image_files(Category, category)
