from django.test import TestCase

from oscar.apps.catalogue.models import Product
from oscar.test.factories.catalogue import ProductFactory


class ProductTestCase(TestCase):
    @staticmethod
    def _get_saved(model_obj):
        model_obj.save()
        model_obj.refresh_from_db()
        return model_obj

    def test_get_meta_title(self):
        parent_title, child_title = "P title", "C title"
        parent_meta_title, child_meta_title = "P meta title", "C meta title"
        parent_product = ProductFactory(
            structure=Product.PARENT, title=parent_title, meta_title=parent_meta_title
        )
        child_product = ProductFactory(
            structure=Product.CHILD,
            title=child_title,
            meta_title=child_meta_title,
            parent=parent_product,
        )
        self.assertEqual(child_product.get_meta_title(), child_meta_title)
        child_product.meta_title = ""
        self.assertEqual(
            self._get_saved(child_product).get_meta_title(), parent_meta_title
        )
        parent_product.meta_title = ""
        child_product.parent = self._get_saved(parent_product)
        self.assertEqual(self._get_saved(child_product).get_meta_title(), child_title)

    def test_get_meta_description(self):
        parent_description, child_description = "P description", "C description"
        parent_meta_description, child_meta_description = (
            "P meta description",
            "C meta description",
        )
        parent_product = ProductFactory(
            structure=Product.PARENT,
            description=parent_description,
            meta_description=parent_meta_description,
        )
        child_product = ProductFactory(
            structure=Product.CHILD,
            description=child_description,
            meta_description=child_meta_description,
            parent=parent_product,
        )
        self.assertEqual(child_product.get_meta_description(), child_meta_description)
        child_product.meta_description = ""
        self.assertEqual(
            self._get_saved(child_product).get_meta_description(),
            parent_meta_description,
        )
        parent_product.meta_description = ""
        child_product.parent = self._get_saved(parent_product)
        self.assertEqual(
            self._get_saved(child_product).get_meta_description(), child_description
        )
