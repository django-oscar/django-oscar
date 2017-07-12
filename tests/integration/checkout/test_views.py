from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from oscar.test.factories import OrderFactory


class ThankYouViewTestCase(TestCase):

    @override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
    def test_analytics_event_triggered_only_on_first_view(self):
        order = OrderFactory()
        session = self.client.session
        # Put the order ID in the session, mimicking a completed order,
        # so that we can reach the thank you page.
        session['checkout_order_id'] = order.pk
        session.save()

        r1 = self.client.get(reverse('checkout:thank-you'))
        self.assertTrue(r1.context['send_analytics_event'])

        # Request the view a second time
        r2 = self.client.get(reverse('checkout:thank-you'))
        self.assertFalse(r2.context['send_analytics_event'])
