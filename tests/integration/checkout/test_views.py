from django.urls import reverse

from oscar.test.factories import OrderFactory
from oscar.test.testcases import WebTestCase


class ThankYouViewTestCase(WebTestCase):
    is_anonymous = True

    def test_analytics_event_triggered_only_on_first_view(self):
        with self.settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            url = reverse("checkout:thank-you")
            order = OrderFactory()
            session = self.client.session
            # Put the order ID in the session, mimicking a completed order,
            # so that we can reach the thank you page.
            session["checkout_order_id"] = order.pk
            session.save()

            r1 = self.client.get(url, follow=True)
            self.assertTrue(r1.context["send_analytics_event"])

            # Request the view a second time
            r2 = self.client.get(url, follow=True)
            self.assertFalse(r2.context["send_analytics_event"])

    def test_missing_order_id_in_the_session(self):
        with self.settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            url = reverse("checkout:thank-you")
            response = self.app.get(url)
            self.assertIsRedirect(response)
            self.assertRedirectsTo(response, "catalogue:index")

    def test_order_id_in_the_session_is_for_a_non_existent_order(self):
        with self.settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            session = self.client.session
            # Put the order ID in the session, mimicking an order that no longer
            # exists, so that we can be redirected to the home page.
            session["checkout_order_id"] = 0
            session.save()

            response = self.client.get(reverse("checkout:thank-you"))
            self.assertRedirects(response, reverse("catalogue:index"))
