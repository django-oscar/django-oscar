from django.test import TestCase

from oscar.apps.promotions import models


class PromotionTest(TestCase):

    def test_default_template_name(self):
        promotion = models.Image.objects.create(name="dummy banner")
        self.assertEqual('promotions/image.html', promotion.template_name())
