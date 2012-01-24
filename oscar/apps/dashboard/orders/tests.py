import httplib

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from oscar.test import ClientTestCase
from oscar.test.helpers import create_order
from oscar.apps.dashboard.orders.forms import OrderSearchForm
from oscar.apps.order.models import Order, OrderNote


class OrderListTests(ClientTestCase):
    is_staff = True

    def test_searching_for_valid_order_number_redirects_to_order_page(self):
        order = create_order()
        fields = OrderSearchForm.base_fields.keys()
        pairs = dict(zip(fields, ['']*len(fields)))
        pairs['order_number'] = order.number
        pairs['response_format'] = 'html'
        url = '%s?%s' % (reverse('dashboard:order-list'), '&'.join(['%s=%s' % (k,v) for k,v in pairs.items()]))
        response = self.client.get(url)
        self.assertEqual(httplib.FOUND, response.status_code)


class OrderDetailTests(ClientTestCase):
    is_staff = True

    def setUp(self):
        self.order = create_order()
        self.url = reverse('dashboard:order-detail', kwargs={'number': self.order.number})
        super(OrderDetailTests, self).setUp()

    def fetch_order(self):
        return Order.objects.get(number=self.order.number)

    def test_order_detail_page_contains_order(self):
        response = self.client.get(self.url)
        self.assertTrue('order' in response.context)

    def test_order_status_change(self):
        params = {'order_action': 'change_order_status',
                  'new_status': 'testing'}
        response = self.client.post(self.url, params)
        self.assertIsRedirect(response)
        self.assertEqual('testing', self.fetch_order().status)

    def test_order_status_change_creates_system_note(self):
        params = {'order_action': 'change_order_status',
                  'new_status': 'testing'}
        response = self.client.post(self.url, params)
        notes = self.order.notes.all()
        self.assertEqual(1, len(notes))
        self.assertEqual(OrderNote.SYSTEM, notes[0].note_type)


