from random import randint
from sys import maxint

from django.test import TestCase
from django.core.exceptions import ValidationError
from oscar.core.compat import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError

from oscar.apps.catalogue.reviews.models import ProductReview, Vote
from oscar.test.factories import create_product


User = get_user_model()


class ProductReviewTests(TestCase):

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

    def test_try_vote_without_login(self):
        self.assertRaises(ValueError, Vote.objects.create, review=self.review, delta=-1, user=self.anon_user)

    def test_try_vote_more_than_once(self):
        vote1 = Vote.objects.create(review=self.review, user=self.user, delta=1)
        self.assertTrue(vote1)
        self.assertRaises(IntegrityError, Vote.objects.create, review=self.review, delta=-1, user=self.user)


