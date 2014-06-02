from six.moves import http_client
from django.conf import settings

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
    is_staff = False

    def test_non_staff_can_only_list_her_orders(self):
        # order-list user1
        response = self.get(reverse('dashboard:order-list'))
        self.assertEqual(set(response.context['orders']),
                         set([self.order_in]))

        # order-detail user2
        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.order_in.number})
        self.assertIsOk(self.get(url))

        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.order_out.number})
        self.assertNoAccess(self.get(url, status="*"))

        # order-line-detail user2
        url = reverse('dashboard:order-line-detail',
                      kwargs={'number': self.order_in.number,
                              'line_id': self.order_in.lines.all()[0].pk})
        self.assertIsOk(self.get(url))
        url = reverse('dashboard:order-line-detail',
                      kwargs={'number': self.order_out.number,
                              'line_id': self.order_out.lines.all()[0].pk})
        self.assertNoAccess(self.get(url, status="*"))

        # order-shipping-address
        url = reverse('dashboard:order-shipping-address',
                      kwargs={'number': self.order_in.number})
        self.assertIsOk(self.get(url))
        url = reverse('dashboard:order-shipping-address',
                      kwargs={'number': self.order_out.number})
        self.assertNoAccess(self.get(url, status="*"))


class PermissionBasedDashboardOrderTestsStaff(PermissionBasedDashboardOrderTestsBase):
    is_staff = True

    def test_staff_user_can_list_all_orders(self):
        orders = [self.order_in, self.order_out]
        # order-list
        response = self.get(reverse('dashboard:order-list'))
        self.assertIsOk(response)
        self.assertEqual(set(response.context['orders']),
                         set(orders))
        # order-detail
        for order in orders:
            url = reverse('dashboard:order-detail',
                          kwargs={'number': order.number})
            self.assertIsOk(self.get(url))


class TestOrderDetailPage(WebTestCase):
    is_staff = True

    def setUp(self):
        super(TestOrderDetailPage, self).setUp()
        # ensures that initial statuses are as expected
        self.order = create_order()
        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.order.number})
        self.page = self.get(url)

    def test_contains_order(self):
        self.assertEquals(self.page.context['order'], self.order)

    def test_allows_notes_to_be_added(self):
        form = self.page.forms['order_note_form']
        form['message'] = "boom"
        response = form.submit()
        self.assertIsRedirect(response)
        notes = self.order.notes.all()
        self.assertEqual(1, len(notes))

    def test_allows_line_status_to_be_changed(self):
        line = self.order.lines.all()[0]
        self.assertEqual(line.status, settings.OSCAR_INITIAL_LINE_STATUS)

        form = self.page.forms['order_lines_form']
        form['line_action'] = 'change_line_statuses'
        form['new_status'] = new_status = 'b'
        form['selected_line'] = [line.pk]
        form.submit()
        # fetch line again
        self.assertEqual(self.order.lines.all()[0].status, new_status)

    def test_allows_order_status_to_be_changed(self):
        form = self.page.forms['order_status_form']
        self.assertEqual(
            self.order.status, settings.OSCAR_INITIAL_ORDER_STATUS)

        form = self.page.forms['order_status_form']
        form['new_status'] = new_status = 'B'
        form.submit()

        # fetch order again
        self.assertEqual(Order.objects.get(pk=self.order.pk).status, new_status)


class TestChangingOrderStatus(WebTestCase):
    is_staff = True

    def setUp(self):
        super(TestChangingOrderStatus, self).setUp()

        Order.pipeline = {'A': ('B', 'C')}
        self.order = create_order(status='A')
        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.order.number})

        page = self.get(url)
        form = page.forms['order_status_form']
        form['new_status'] = 'B'
        self.response = form.submit()

    def reload_order(self):
        return Order.objects.get(number=self.order.number)

    def test_works(self):
        self.assertIsRedirect(self.response)
        self.assertEqual('B', self.reload_order().status)

    def test_creates_system_note(self):
        notes = self.order.notes.all()
        self.assertEqual(1, len(notes))
        self.assertEqual(OrderNote.SYSTEM, notes[0].note_type)


class LineDetailTests(WebTestCase):
    is_staff = True

    def setUp(self):
        self.order = create_order()
        self.line = self.order.lines.all()[0]
        self.url = reverse('dashboard:order-line-detail',
                           kwargs={'number': self.order.number,
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
