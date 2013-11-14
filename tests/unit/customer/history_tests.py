from django.test import TestCase
from django import http

from oscar.apps.customer import history


class TestProductHistory(TestCase):

    def setUp(self):
        self.request = http.HttpRequest()
        self.response = http.HttpResponse()

    def test_starts_with_empty_list(self):
        products = history.get(self.request)
        self.assertEqual([], products)
