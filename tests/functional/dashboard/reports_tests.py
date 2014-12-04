from django.core.urlresolvers import reverse

from oscar.test.testcases import WebTestCase


class ReportsDashboardTests(WebTestCase):
    is_staff = True

    def test_dashboard_is_accessible_to_staff(self):
        url = reverse('dashboard:reports-index')
        response = self.get(url)
        self.assertIsOk(response)
