from django.urls import reverse

from oscar.test.testcases import WebTestCase


class ReportsDashboardTests(WebTestCase):
    is_staff = True

    def test_dashboard_is_accessible_to_staff(self):
        url = reverse("dashboard:reports-index")
        response = self.get(url)
        self.assertIsOk(response)

    def test_conditional_offers_no_date_range(self):
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.form["report_type"] = "conditional-offers"
        response.form.submit()
        self.assertIsOk(response)

    def test_conditional_offers_with_date_range(self):
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.form["report_type"] = "conditional-offers"
        response.form["date_from"] = "2017-01-01"
        response.form["date_to"] = "2017-12-31"
        response.form.submit()
        self.assertIsOk(response)

    def test_conditional_offers_with_date_range_download(self):
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.form["report_type"] = "conditional-offers"
        response.form["date_from"] = "2017-01-01"
        response.form["date_to"] = "2017-12-31"
        response.form["download"] = "true"
        response.form.submit()
        self.assertIsOk(response)
