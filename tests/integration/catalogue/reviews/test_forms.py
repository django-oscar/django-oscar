from django.test import TestCase

from oscar.apps.catalogue.reviews import forms
from oscar.test.factories import UserFactory, create_product


class TestReviewForm(TestCase):
    def test_cleans_title(self):
        product = create_product()
        reviewer = UserFactory()
        data = {
            "title": "  This product is lovely",
            "body": "I really like this cheese",
            "score": 0,
            "name": "JR Hartley",
            "email": "hartley@example.com",
        }
        form = forms.ProductReviewForm(product=product, user=reviewer, data=data)

        assert form.is_valid()

        review = form.save()
        assert review.title == "This product is lovely"

    def test_validates_empty_data_correctly(self):
        form = forms.ProductReviewForm(product=None, user=None, data={})
        assert form.is_valid() is False

    def test_validates_correctly(self):
        data = {
            "title": "This product is lovely",
            "body": "I really like this cheese",
            "score": 0,
            "name": "JR Hartley",
            "email": "hartley@example.com",
        }
        form = forms.ProductReviewForm(product=None, user=None, data=data)
        assert form.is_valid()


class TestVoteForm(TestCase):
    def setUp(self):
        self.product = create_product()
        self.reviewer = UserFactory()
        self.voter = UserFactory()
        self.review = self.product.reviews.create(
            title="This is nice", score=3, body="This is the body", user=self.reviewer
        )

    def test_allows_real_users_to_vote(self):
        form = forms.VoteForm(self.review, self.voter, data={"delta": 1})
        self.assertTrue(form.is_valid())

    def test_prevents_users_from_voting_more_than_once(self):
        self.review.vote_up(self.voter)
        form = forms.VoteForm(self.review, self.voter, data={"delta": 1})
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors["__all__"]) > 0)

    def test_prevents_users_voting_on_their_own_reviews(self):
        form = forms.VoteForm(self.review, self.reviewer, data={"delta": 1})
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors["__all__"]) > 0)
