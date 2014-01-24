from django.test import TestCase
from django.core.exceptions import ValidationError
from django_dynamic_fixture import G
from nose.plugins.attrib import attr

from oscar.core.compat import get_user_model
from oscar.apps.catalogue.reviews import models
from oscar.test.factories import create_product

User = get_user_model()


@attr('reviews')
class TestAnAnonymousReview(TestCase):

    def setUp(self):
        self.product = create_product()
        self.data = {
            'product': self.product,
            'title': 'This product is lovely',
            'body': 'I really like this cheese',
            'score': 0,
            'name': 'JR Hartley',
            'email': 'hartley@example.com'
        }

    def review(self, **kwargs):
        if kwargs:
            data = self.data.copy()
            data.update(kwargs)
        else:
            data = self.data
        return models.ProductReview(**data)

    def test_can_be_created(self):
        review = self.review()
        review.full_clean()

    def test_requires_a_title(self):
        review = self.review(title="")
        self.assertRaises(ValidationError, review.full_clean)

    def test_requires_a_body(self):
        review = self.review(body="")
        self.assertRaises(ValidationError, review.full_clean)

    def test_requires_a_name(self):
        review = self.review(name="")
        self.assertRaises(ValidationError, review.full_clean)

    def test_requires_an_email_address(self):
        review = self.review(email="")
        self.assertRaises(ValidationError, review.full_clean)

    def test_requires_non_whitespace_title(self):
        review = self.review(title="    ")
        self.assertRaises(ValidationError, review.full_clean)

    def test_starts_with_no_votes(self):
        review = self.review()
        review.save()
        self.assertFalse(review.has_votes)
        self.assertEqual(0, review.num_up_votes)
        self.assertEqual(0, review.num_down_votes)

    def test_has_reviewer_name_property(self):
        review = self.review(name="Dave")
        self.assertEqual("Dave", review.reviewer_name)


@attr('reviews')
class TestAUserReview(TestCase):

    def setUp(self):
        self.product = create_product()
        self.user = G(User, first_name="Tom", last_name="Thumb")
        self.data = {
            'product': self.product,
            'title': 'This product is lovely',
            'body': 'I really like this cheese',
            'score': 0,
            'user': self.user
        }

    def review(self, **kwargs):
        if kwargs:
            data = self.data.copy()
            data.update(kwargs)
        else:
            data = self.data
        return models.ProductReview(**data)

    def test_can_be_created(self):
        review = self.review()
        review.full_clean()

    def test_requires_a_title(self):
        review = self.review(title="")
        self.assertRaises(ValidationError, review.full_clean)

    def test_requires_a_body(self):
        review = self.review(body="")
        self.assertRaises(ValidationError, review.full_clean)

    def test_has_reviewer_name_property(self):
        review = self.review()
        self.assertEqual("Tom Thumb", review.reviewer_name)


@attr('reviews')
class TestVotingOnAReview(TestCase):

    def setUp(self):
        self.product = create_product()
        self.user = G(User)
        self.voter = G(User)
        self.review = self.product.reviews.create(
            title='This is nice',
            score=3,
            body="This is the body",
            user=self.user)

    def test_updates_totals_for_upvote(self):
        self.review.vote_up(self.voter)
        self.assertTrue(self.review.has_votes)
        self.assertEqual(1, self.review.total_votes)
        self.assertEqual(1, self.review.delta_votes)

    def test_updates_totals_for_downvote(self):
        self.review.vote_down(self.voter)
        self.assertTrue(self.review.has_votes)
        self.assertEqual(1, self.review.total_votes)
        self.assertEqual(-1, self.review.delta_votes)

    def test_is_permitted_for_normal_user(self):
        is_allowed, reason = self.review.can_user_vote(self.voter)
        self.assertTrue(is_allowed, reason)

    def test_is_not_permitted_for_reviewer(self):
        is_allowed, reason = self.review.can_user_vote(self.user)
        self.assertFalse(is_allowed, reason)

    def test_is_not_permitted_for_previous_voter(self):
        self.review.vote_up(self.voter)
        is_allowed, reason = self.review.can_user_vote(self.voter)
        self.assertFalse(is_allowed, reason)
