import httplib

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django_dynamic_fixture import get

from oscar.test.testcases import ClientTestCase, WebTestCase
from oscar.test.factories import create_order
from oscar.apps.order.models import Order, OrderNote, ShippingAddress
from oscar.core.compat import get_user_model


User = get_user_model()


class TestOrderListDashboard(WebTestCase):
    is_staff = True

    def test_redirects_to_detail_page(self):
        order = create_order()
        page = self.get(reverse('dashboard:order-list'))
        form = page.forms['search_form']
        form['order_number'] = order.number
        response = form.submit()
        self.assertEqual(httplib.FOUND, response.status_code)

    def test_downloads_to_csv_without_error(self):
        address = get(ShippingAddress)
        create_order(shipping_address=address)
        page = self.get(reverse('dashboard:order-list'))
        form = page.forms['orders_form']
        form['selected_order'].checked = True
        form.submit('download_selected')


class OrderDetailTests(ClientTestCase):
    is_staff = True

    def setUp(self):
        Order.pipeline = {'A': ('B', 'C')}
        self.order = create_order(status='A')
        self.url = reverse('dashboard:order-detail', kwargs={'number': self.order.number})
        super(OrderDetailTests, self).setUp()

    def fetch_order(self):
        return Order.objects.get(number=self.order.number)

    def test_order_detail_page_contains_order(self):
        response = self.client.get(self.url)
        self.assertTrue('order' in response.context)

    def test_order_status_change(self):
        params = {'order_action': 'change_order_status',
                  'new_status': 'B'}
        response = self.client.post(self.url, params)
        self.assertIsRedirect(response)
        self.assertEqual('B', self.fetch_order().status)

    def test_order_status_change_creates_system_note(self):
        params = {'order_action': 'change_order_status',
                  'new_status': 'B'}
        self.client.post(self.url, params)
        notes = self.order.notes.all()
        self.assertEqual(1, len(notes))
        self.assertEqual(OrderNote.SYSTEM, notes[0].note_type)


class LineDetailTests(ClientTestCase):
    is_staff = True

    def setUp(self):
        self.order = create_order()
        self.line = self.order.lines.all()[0]
        self.url = reverse('dashboard:order-line-detail', kwargs={'number': self.order.number,
                                                                  'line_id': self.line.id})
        super(LineDetailTests, self).setUp()

    def test_line_detail_page_exists(self):
        response = self.client.get(self.url)
        self.assertIsOk(response)

    def test_line_in_context(self):
        response = self.client.get(self.url)
        self.assertInContext(response, 'line')


class TemplateTagTests(TestCase):
    def test_get_num_orders(self):
        user = get(User)
        for i in range(1, 4):
            get(Order, user=user)
        out = Template(
            "{% load dashboard_tags %}"
            "{% num_orders user %}"
        ).render(Context({
            'user': user
        }))
        self.assertEquals(out, "3")
