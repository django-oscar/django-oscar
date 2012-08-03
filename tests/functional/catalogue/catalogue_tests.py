import httplib

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from oscar.test.helpers import create_product


class TestProductDetailView(TestCase):

    def setUp(self):
        self.client = Client()

    def test_enforces_canonical_url(self):
        p = create_product()
        args = {'product_slug': 'wrong-slug',
                'pk': p.id}
        wrong_url = reverse('catalogue:detail', kwargs=args)
        response = self.client.get(wrong_url)
        self.assertEquals(httplib.MOVED_PERMANENTLY, response.status_code)
