from django.utils import unittest

from oscar.promotions.models import * 


class PromotionTest(unittest.TestCase):

    def test_promotion_cannot_be_saved_without_content(self):
        pass


class PagePromotionTest(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_click_is_recorded(self):
        promotion = Promotion.objects.create(name="Dummy promotion")
        promotion.record_click()
        self.assertTrue(1, promotion.clicks)


