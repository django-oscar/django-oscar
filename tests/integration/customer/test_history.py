from django import http
from django.test import TestCase

from oscar.core.loading import get_class

CustomerHistoryManager = get_class("customer.history", "CustomerHistoryManager")


class TestProductHistory(TestCase):
    def setUp(self):
        self.request = http.HttpRequest()
        self.response = http.HttpResponse()

    def test_starts_with_empty_list(self):
        products = CustomerHistoryManager.get(self.request)
        self.assertEqual([], products)
