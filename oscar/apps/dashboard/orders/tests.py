import httplib

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from oscar.test import ClientTestCase
from oscar.test.helpers import create_order
from oscar.apps.dashboard.orders.forms import OrderSearchForm


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

    def test_order_detail_page_contains_order(self):
        order = create_order()
        url = reverse('dashboard:order-detail', kwargs={'number': order.number})
        response = self.client.get(url)
        self.assertTrue('order' in response.context)

