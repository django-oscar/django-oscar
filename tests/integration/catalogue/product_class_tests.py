from django.test import TestCase

from oscar.apps.catalogue import models


class TestProductClassModel(TestCase):

    def test_slug_is_auto_created(self):
        books = models.ProductClass.objects.create(
            name="Book",
        )
        self.assertEqual('book', books.slug)

    def test_has_attribute_for_whether_shipping_is_required(self):
        models.ProductClass.objects.create(
            name="Download",
            requires_shipping=False,
        )
