import httplib

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve
from django.test import Client

from oscar.apps.promotions.models import * 


class PromotionTest(TestCase):

    def test_default_template_name(self):
        promotion = Image.objects.create(name="dummy banner")
        self.assertEqual('promotions/image.html', promotion.template_name())





#class PagePromotionTest(unittest.TestCase):
#    
#    def setUp(self):
#        self.promotion = Promotion.objects.create(name='Dummy', link_url='http://www.example.com')
#        self.page_prom = PagePromotion.objects.create(promotion=self.promotion,
#                                                      position=RAW_HTML,
#                                                      page_url='/')
#    
#    def test_clicks_start_at_zero(self):
#        self.assertEquals(0, self.page_prom.clicks)
#    
#    def test_click_is_recorded(self):
#        self.page_prom.record_click()
#        self.assertEquals(1, self.page_prom.clicks)
#
#    def test_get_link(self):
#        link = self.page_prom.get_link()
#        match = resolve(link)
#        self.assertEquals('page-click', match.url_name)
#
#
#class KeywordPromotionTest(unittest.TestCase):
#    
#    def setUp(self):
#        self.promotion = Promotion.objects.create(name='Dummy', link_url='http://www.example.com')
#        self.kw_prom = KeywordPromotion.objects.create(promotion=self.promotion,
#                                                       position=RAW_HTML,
#                                                       keyword='cheese')
#    
#    def test_clicks_start_at_zero(self):
#        self.assertEquals(0, self.kw_prom.clicks)
#    
#    def test_click_is_recorded(self):
#        self.kw_prom.record_click()
#        self.assertEquals(1, self.kw_prom.clicks)
#        
#    def test_get_link(self):
#        link = self.kw_prom.get_link()
#        match = resolve(link)
#        self.assertEquals('keyword-click', match.url_name)
        
