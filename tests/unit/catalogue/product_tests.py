from django.test import TestCase

from oscar.apps.catalogue import models


class TestProductModel(TestCase):

    def test_defaults_to_zero_score(self):
        p = models.Product()
        self.assertEqual(0, p.score)
