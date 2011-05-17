import unittest
from random import randint
from sys import maxint
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, AnonymousUser
from django.db import IntegrityError

from oscar.product.models import Item, ItemClass
from oscar.reviews.models import ProductReview, Vote


class ProductReviewTests(unittest.TestCase):

    def setUp(self):
        username = str(randint(0, maxint))  
        self.user = User.objects.create_user(username, '%s@users.com'%username, '%spass123'%username)
        self.anon_user = AnonymousUser()
        self.item_class,_ = ItemClass.objects.get_or_create(name='Books')
        self.item,_ = Item.objects.get_or_create(title='Django Book v2', item_class=self.item_class)
        self.review,_ = ProductReview.objects.get_or_create(title='Django Book v2 Review',\
                            product=self.item, user=self.user, score=3)

class TopLevelProductReviewTests(ProductReviewTests):
    
    def test_top_level_reviews_must_have_titles_and_scores(self):
        self.assertRaises(ValidationError, ProductReview.objects.create, product=self.item,\
                           user=self.user)
    
    def test_top_level_anonymous_reviews_must_have_names_and_emails(self):
        self.assertRaises(ValidationError, ProductReview.objects.create, product=self.item,\
                           user=None, title="Anonymous review", score=3)
        

class TopLevelProductReviewVoteTests(ProductReviewTests):
    
    def setUp(self):
        super(TopLevelProductReviewVoteTests, self).setUp()
    
    def test_try_vote_without_login(self):        
        self.assertRaises(ValueError, Vote.objects.create, review=self.review, user=self.anon_user)
    
    def test_try_vote_more_than_once(self):
        vote1 = Vote.objects.create(review=self.review, user=self.user, up=1)         
        self.assertRaises(IntegrityError, Vote.objects.create, review=self.review, user=self.user)
        
    
class SingleProductReviewViewTest(ProductReviewTests):
    u"""
    Each product has reviews attached to it
    """
    fixtures = ['sample-products, sample-reviews']
    
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

class ProductReviewVotingActionTests(TestCase):
    u"""
    Includes the behaviour tests after voting on a review
    """
    fixtures = ['sample-product', 'sample-reviews']    
    
    def setUp(self):
        # reviews sorted by votes
        self.reviews = ProductReview.top_voted.all()        
        # dummy voters
        self.voters = 10        
        self.users = []
        for i in xrange(self.voters):
            u = User.objects.create_user('user%d'%i, 'user%d@users.com'%i, 'userpass%d'%i)
            self.users.append(u)        
    
    def test_upvote_can_boost_up_review(self):
        # get a review which has lowest vote
        self.review = self.reviews.reverse()[0]
        self.assertTrue(self.review)
        review_id = self.review.id
        old_votes = self.review.up_votes
        old_rank = list(self.reviews.values_list('id', flat=True)).index(review_id)       
        # vote up
        for i in xrange(self.voters):
            vote = Vote.objects.create(review=self.review, user=self.users[i], up=1)
            self.assertTrue(vote)
        # test vote count
        self.failUnlessEqual(self.review.up_votes, (self.voters + old_votes))
        # test rank
        reviews = ProductReview.top_voted.all()
        new_rank = list(reviews.values_list('id', flat=True)).index(review_id)
        self.failUnless(new_rank < old_rank)
   