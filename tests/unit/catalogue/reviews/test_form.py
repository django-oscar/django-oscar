from django.test import TestCase

from oscar.apps.catalogue.reviews import forms


class TestReviewForm(TestCase):

    def setUp(self):
        self.data = {
            'title': 'This product is lovely',
            'body': 'I really like this cheese',
            'score': 0,
            'name': 'JR Hartley',
            'email': 'hartley@example.com'
        }

    def form(self, **kwargs):
        data = self.data.copy()
        data.update(kwargs)
        return forms.ProductReviewForm(product=None, user=None, data=data)

    def test_validates_empty_data_correctly(self):
        forms.ProductReviewForm(product=None, user=None, data={}).is_valid()

    def test_validates_correctly(self):
        self.assertTrue(self.form().is_valid())
