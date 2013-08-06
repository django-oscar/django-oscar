from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.catalogue.reviews import models
from oscar.test.factories import create_product


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
