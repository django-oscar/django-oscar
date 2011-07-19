from random import randint
from sys import maxint

from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, AnonymousUser
from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.utils import unittest

from oscar.apps.catalogue.reviews.models import ProductReview, Vote
from oscar.test.helpers import create_product


class ProductReviewTests(unittest.TestCase):
    u"""
    Basic setup
    """
    def setUp(self):
        username = str(randint(0, maxint))
        self.user = User.objects.create_user(username, '%s@users.com'%username, '%spass123'%username)
        self.anon_user = AnonymousUser()
        self.product = create_product()
        self.review = ProductReview.objects.create(product=self.product,
                                                   title="Dummy review",
                                                   score=3,
                                                   user=self.user)

    def test_top_level_reviews_must_have_titles_and_scores(self):
        self.assertRaises(ValidationError, ProductReview.objects.create, product=self.product,
                          user=self.user)

    def test_top_level_anonymous_reviews_must_have_names_and_emails(self):
        self.assertRaises(ValidationError, ProductReview.objects.create, product=self.product,
                          user=None, title="Anonymous review", score=3)


class TopLevelProductReviewVoteTests(ProductReviewTests):
    """
    Basic tests for Vote model
    """

    def test_try_vote_without_login(self):
        self.assertRaises(ValueError, Vote.objects.create, review=self.review, delta=-1, user=self.anon_user)

    def test_try_vote_more_than_once(self):
        vote1 = Vote.objects.create(review=self.review, user=self.user, delta=1)
        self.assertTrue(vote1)
        self.assertRaises(IntegrityError, Vote.objects.create, review=self.review, delta=-1, user=self.user)


class SingleProductReviewViewTest(ProductReviewTests, TestCase):
    u"""
    Tests for each product review 
    """
    def setUp(self):
        self.client = Client()
        super(SingleProductReviewViewTest, self).setUp()
        self.kwargs = {
                'product_slug': self.product.slug,
                'pk': str(self.product.id)}
        
    def test_each_product_has_review(self):
        url = reverse('catalogue:detail', kwargs=self.kwargs)
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
    
    def test_user_can_add_product_review(self):
        kwargs = {
                'product_slug': self.product.slug,
                'product_pk': str(self.product.id)}
        url = reverse('catalogue:reviews-add', kwargs=kwargs)
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

