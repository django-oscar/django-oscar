from random import randint
from sys import maxint
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, AnonymousUser
from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.utils import unittest

from oscar.apps.product.models import Item, ItemClass
from oscar.apps.reviews.models import ProductReview, Vote


class ProductReviewTests(unittest.TestCase):
    u"""
    Basic setup
    """
    def setUp(self):
        username = str(randint(0, maxint))
        self.user = User.objects.create_user(username, '%s@users.com'%username, '%spass123'%username)
        self.anon_user = AnonymousUser()
        self.item_class,_ = ItemClass.objects.get_or_create(name='Books')
        self.item,_ = Item.objects.get_or_create(title='Django Book v2', item_class=self.item_class)
        self.review,_ = ProductReview.objects.get_or_create(title='Django Book v2 Review',\
                            product=self.item, user=self.user, score=3, approved=True)


class TopLevelProductReviewTests(ProductReviewTests):
    u"""
    Basic tests for ProductReview model
    """
    def test_top_level_reviews_must_have_titles_and_scores(self):
        self.assertRaises(ValidationError, ProductReview.objects.create, product=self.item,\
                           user=self.user)

    def test_top_level_anonymous_reviews_must_have_names_and_emails(self):
        self.assertRaises(ValidationError, ProductReview.objects.create, product=self.item,\
                           user=None, title="Anonymous review", score=3)


class TopLevelProductReviewVoteTests(ProductReviewTests):
    u"""
    Basic tests for Vote model
    """
    def setUp(self):
        super(TopLevelProductReviewVoteTests, self).setUp()

    def test_top_level_vote_must_have_choice(self):
        self.assertRaises(ValidationError, Vote.objects.create, review=self.review,\
                           user=self.user)

    def test_try_vote_without_login(self):
        self.assertRaises(ValueError, Vote.objects.create, review=self.review, choice =-1, user=self.anon_user)

    def test_try_vote_more_than_once(self):
        vote1 = Vote.objects.create(review=self.review, user=self.user, choice=1)
        self.assertTrue(vote1)
        self.assertRaises(IntegrityError, Vote.objects.create, review=self.review, choice=-1, user=self.user)


class SingleProductReviewViewTest(ProductReviewTests, TestCase):
    u"""
    Tests for each product review 
    """
    def setUp(self):
        self.client = Client()
        super(SingleProductReviewViewTest, self).setUp()
        self.kwargs = {'item_class_slug': self.item.get_item_class().slug,
                'item_slug': self.item.slug,
                'item_id': str(self.item.id)}
        
    def test_each_product_has_review(self):
        url = reverse('oscar-product-item', kwargs=self.kwargs)
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
    
    def test_user_can_add_product_review(self):
        url = reverse('oscar-product-review-add', kwargs=self.kwargs)
        self.client.login(username='testuser', password='secret')
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
        # check necessary review fields for logged in user
        self.assertContains(response, 'title')
        self.assertContains(response, 'score')
        # check additional fields for anonymous user
        self.client.login(username=None)
        response = self.client.get(url)
        self.assertContains(response, 'name')
        self.assertContains(response, 'email')
        
    def test_each_review_has_own_page(self):  # FIXME: broken for reverse
        self.kwargs['review_id'] = self.review.id
        url = reverse('oscar-product-review', kwargs = self.kwargs)
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)


class SingleProductReviewVoteViewTest(ProductReviewTests, TestCase):
    u"""
    Each product review can be voted up or down
    """
    def setUp(self):
        self.client = Client()
        super(SingleProductReviewVoteViewTest, self).setUp()   
        self.kwargs = {'item_class_slug': self.item.get_item_class().slug, 
                'item_slug': self.item.slug,
                'item_id': self.item.id,
                'review_id': self.review.id}
        
    def test_vote_up_product_review(self):
        url = reverse('oscar-vote-review', kwargs=self.kwargs)
        self.client.login(username='testuser', password='secret')
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
    

class ProductReviewVotingActionTests(TestCase):
    u"""
    Includes the behaviour tests after voting on a review
    """
    fixtures = ['sample-product', 'sample-reviews']    
    
    def setUp(self):
        # get reviews
        self.reviews = ProductReview.objects.all()       
        # dummy voters
        self.voters = 10        
        self.users = []
        for i in xrange(self.voters):
            u = User.objects.create_user('user%d'%i, 'user%d@users.com'%i, 'userpass%d'%i)
            self.users.append(u)        
    
    def test_upvote_can_boost_up_review(self):
        # get a review
        old_rank = 1
        self.assertTrue(self.reviews)
        self.review = self.reviews[old_rank]        
        review_id = self.review.id
        old_votes = self.review.total_votes
        # vote up
        for i in xrange(self.voters):
            vote = Vote.objects.create(review=self.review, user=self.users[i], choice=1)
            self.assertTrue(vote)
        # test vote count
        self.failUnlessEqual(self.review.total_votes, (self.voters + old_votes))
        # test rank
        reviews = ProductReview.top_voted.all()
        new_rank = list(reviews.values_list('id', flat=True)).index(review_id)
        self.failUnless(new_rank < old_rank)
