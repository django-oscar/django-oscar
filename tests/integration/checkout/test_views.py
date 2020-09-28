from django.urls import reverse

from oscar.test.factories import OrderFactory
from oscar.test.testcases import WebTestCase


class ThankYouViewTestCase(WebTestCase):
    is_anonymous = False

    def test_analytics_event_triggered_only_on_first_view(self):
        with self.settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            url = reverse('checkout:thank-you')
            order = OrderFactory()
            session = self.client.session
            # Put the order ID in the session, mimicking a completed order,
            # so that we can reach the thank you page.
            session['checkout_order_id'] = order.pk
            session.save()

            r1 = self.client.get(url, follow=True)
            self.assertTrue(r1.context['send_analytics_event'])

            # Request the view a second time
            r2 = self.client.get(url, follow=True)
            self.assertFalse(r2.context['send_analytics_event'])

    def test_missing_order_id_in_the_session(self):
        with self.settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            url = reverse('checkout:thank-you')
            response = self.app.get(url)
            self.assertIsRedirect(response)
            self.assertRedirectsTo(response, 'catalogue:index')
