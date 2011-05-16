import unittest

from django.test import TestCase, Client
from django.core.exceptions import ValidationError

from oscar.product.models import Item, ItemClass
from oscar.reviews.models import ProductReview, Vote


class ProductReviewTests(unittest.TestCase):

    def setUp(self):
        self.item_class,_ = ItemClass.objects.get_or_create(name='Books')
        self.item,_ = Item.objects.get_or_create(title='Django Book v2', item_class=self.item_class)
        self.review,_ = ProductReview.objects.get_or_create(title='Django Book v2 Review', product=self.item)
   

class TopLevelProductReviwTests(ProductReviewTests):
    
    def test_top_level_reviews_must_have_titles(self):
        self.assertRaises(ValidationError, ProductReview.objects.create, product=self.item)


class TopLevelProductReviwVoteTests(ProductReviewTests):
    
    def test_top_level_vote_must_be_up_or_down(self):
        self.assertRaises(ValidationError, Vote.objects.create, review=self.review)
    
    def test_try_vote_without_login(self):
        pass
    
    def test_try_vote_more_than_once(self):
        pass
    
    def test_review_boost_up_after_voteup(self):
        pass
    
    def test_review_boost_down_after_votedown(self):
        pass
    
    
class SingleProductReviewViewTest(TestCase):
    u"""
    Each product has reviews attached to it
    """
    fixtures = ['sample-products-with-reviews']
    
    def setUp(self):
        self.client = Client()
    
    def test_each_product_has_review(self):
        pass
    
    def test_each_review_has_own_page(self):
        pass
    
    def test_product_page_shows_correct_avg_score(self):
        pass
    
    def test_product_page_shows_eligible_reviews(self):
        u"""
        Based on settings.OSCAR_MODERATE_REVIEWS 
        """
        pass
    
    
    
    
    
    
    
    
    
    
    