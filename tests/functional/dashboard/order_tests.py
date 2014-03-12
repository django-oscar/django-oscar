from six.moves import http_client

from oscar.core.loading import get_model
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django_dynamic_fixture import get, G

from oscar.test.testcases import WebTestCase
from oscar.test.factories import create_order, create_basket
from oscar.apps.order.models import Order, OrderNote
from oscar.core.compat import get_user_model


User = get_user_model()
Basket = get_model('basket', 'Basket')
Partner = get_model('partner', 'Partner')
ShippingAddress = get_model('order', 'ShippingAddress')


class TestOrderListDashboard(WebTestCase):
    is_staff = True

    def test_redirects_to_detail_page(self):
        order = create_order()
        page = self.get(reverse('dashboard:order-list'))
        form = page.forms['search_form']
        form['order_number'] = order.number
        response = form.submit()
        self.assertEqual(http_client.FOUND, response.status_code)

    def test_downloads_to_csv_without_error(self):
        address = get(ShippingAddress)
        create_order(shipping_address=address)
        page = self.get(reverse('dashboard:order-list'))
        form = page.forms['orders_form']
        form['selected_order'].checked = True
        form.submit('download_selected')

    def test_allows_order_number_search(self):
        page = self.get(reverse('dashboard:order-list'))
        form = page.forms['search_form']
        form['order_number'] = '+'
        form.submit()


class PermissionBasedDashboardOrderTestsBase(WebTestCase):
    permissions = ['partner.dashboard_access', ]
    username = 'user1@example.com'

    def setUp(self):
        """
        Creates two orders. order_in has self.user in it's partner users list.
        """
        super(PermissionBasedDashboardOrderTestsBase, self).setUp()
        self.address = G(ShippingAddress)
        self.basket_in = create_basket()
        self.basket_out = create_basket()
        # replace partner with one that has the user in it's users list
        self.partner_in = G(Partner, users=[self.user])
        stockrecord = self.basket_in.lines.all()[0].stockrecord
        stockrecord.partner = self.partner_in
        stockrecord.save()

        self.order_in = create_order(basket=self.basket_in,
                                     shipping_address=self.address)
        self.order_out = create_order(basket=self.basket_out,
                                      shipping_address=self.address)


class PermissionBasedDashboardOrderTestsNoStaff(PermissionBasedDashboardOrderTestsBase):

    def test_non_staff_can_only_list_her_orders(self):
        # order-list user1
        self.client.login(email='user1@example.com', password=self.password)
        response = self.client.get(reverse('dashboard:order-list'))
        self.assertEqual(set(response.context['orders']),
                         set([self.order_in]))
        # order-detail user2
        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.order_in.number})
        self.assertIsOk(self.client.get(url))
        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.order_out.number})
        self.assertNoAccess(self.client.get(url))
        # order-line-detail user2
        url = reverse('dashboard:order-line-detail',
                      kwargs={'number': self.order_in.number,
                              'line_id': self.order_in.lines.all()[0].pk})
        self.assertIsOk(self.client.get(url))
        url = reverse('dashboard:order-line-detail',
                      kwargs={'number': self.order_out.number,
                              'line_id': self.order_out.lines.all()[0].pk})
        self.assertNoAccess(self.client.get(url))
        # order-shipping-address
        url = reverse('dashboard:order-shipping-address',
                      kwargs={'number': self.order_in.number})
        self.assertIsOk(self.client.get(url))
        url = reverse('dashboard:order-shipping-address',
                      kwargs={'number': self.order_out.number})
        self.assertNoAccess(self.client.get(url))


class PermissionBasedDashboardOrderTestsStaff(PermissionBasedDashboardOrderTestsBase):
    is_staff = True

    def test_staff_user_can_list_all_orders(self):
        orders = [self.order_in, self.order_out]
        # order-list
        response = self.client.get(reverse('dashboard:order-list'))
        self.assertIsOk(response)
        self.assertEqual(set(response.context['orders']),
                         set(orders))
        # order-detail
        for order in orders:
            url = reverse('dashboard:order-detail',
                          kwargs={'number': order.number})
            self.assertIsOk(self.get(url))


class OrderDetailTests(WebTestCase):
    is_staff = True

    def setUp(self):
        Order.pipeline = {'A': ('B', 'C')}
        self.order = create_order(status='A')
        self.url = reverse('dashboard:order-detail', kwargs={'number': self.order.number})
        super(OrderDetailTests, self).setUp()

    def fetch_order(self):
        return Order.objects.get(number=self.order.number)

    def test_order_detail_page_contains_order(self):
        response = self.get(self.url)
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


class LineDetailTests(WebTestCase):
    is_staff = True

    def setUp(self):
        self.order = create_order()
        self.line = self.order.lines.all()[0]
        self.url = reverse('dashboard:order-line-detail', kwargs={'number': self.order.number,
                                                                  'line_id': self.line.id})
        super(LineDetailTests, self).setUp()

    def test_line_detail_page_exists(self):
        response = self.get(self.url)
        self.assertIsOk(response)

    def test_line_in_context(self):
        response = self.get(self.url)
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
        self.assertEqual(out, "3")
