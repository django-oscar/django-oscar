from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
import mock

from oscar.apps.checkout.utils import CheckoutSessionData


class TestCheckoutSession(TestCase):
    """
    oscar.apps.checkout.utils.CheckoutSessionData
    """

    def setUp(self):
        request = RequestFactory().get('/')
        SessionMiddleware().process_request(request)
        self.session_data = CheckoutSessionData(request)

    def test_allows_data_to_be_written_and_read_out(self):
        self.session_data._set('namespace', 'key', 'value')
        self.assertEqual('value', self.session_data._get('namespace', 'key'))

    def test_allows_set_data_can_be_unset(self):
        self.session_data._set('namespace', 'key', 'value')
        self.session_data._unset('namespace', 'key')
        self.assertIsNone(self.session_data._get('namespace', 'key'))

    def test_stores_guest_email(self):
        self.session_data.set_guest_email('a@a.com')
        self.assertEqual('a@a.com', self.session_data.get_guest_email())

    def test_allows_a_namespace_to_be_flushed(self):
        self.session_data._set('ns', 'a', 1)
        self.session_data._set('ns', 'b', 2)
        self.session_data._flush_namespace('ns')
        self.assertIsNone(self.session_data._get('ns', 'a'))
        self.assertIsNone(self.session_data._get('ns', 'b'))

    def test_allows_bill_to_user_address(self):
        address = mock.Mock()
        address.id = 1
        self.session_data.bill_to_user_address(address)
        self.assertEqual(1, self.session_data.billing_user_address_id())
