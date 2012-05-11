from django.test import TestCase
from django.core.urlresolvers import reverse

from oscar.test import ClientTestCase


class ReviewsDashboardTests(ClientTestCase):
    is_staff = True

    def test_reviews_dashboard_is_accessible_to_staff(self):
        url = reverse('dashboard:reviews-index')
        response = self.client.get(url)
        self.assertIsOk(response)
