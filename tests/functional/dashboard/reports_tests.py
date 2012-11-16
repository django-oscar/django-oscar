from django.test import TestCase
from django.core.urlresolvers import reverse

from oscar_testsupport.testcases import ClientTestCase


class ReportsDashboardTests(ClientTestCase):
    is_staff = True

    def test_dashboard_is_accessible_to_staff(self):
        url = reverse('dashboard:reports-index')
        response = self.client.get(url)
        self.assertIsOk(response)