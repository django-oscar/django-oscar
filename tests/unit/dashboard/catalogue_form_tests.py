from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.catalogue import models
from oscar.apps.dashboard.catalogue import forms


class TestCreateProductForm(TestCase):

    def setUp(self):
        self.pclass = G(models.ProductClass)

    def submit(self, data):
        return forms.ProductForm(self.pclass, data=data)

    def test_validates_that_parent_products_must_have_title(self):
        form = self.submit({})
        self.assertFalse(form.is_valid())

    def test_validates_that_child_products_dont_need_a_title(self):
        parent = G(models.Product, product_class=self.pclass, parent=None)
        form = self.submit({'parent': parent.id})
        self.assertTrue(form.is_valid())
