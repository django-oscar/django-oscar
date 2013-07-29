from django.db.models import get_model

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django_dynamic_fixture import get, G

from oscar.test.testcases import ClientTestCase
from oscar.test.factories import create_order, create_product
from oscar.apps.order.models import Order, OrderNote
from oscar.core.compat import get_user_model


User = get_user_model()
Basket = get_model('basket', 'Basket')
Partner = get_model('partner', 'Partner')
ShippingAddress = get_model('order', 'ShippingAddress')

class OrderListTests(ClientTestCase):
    is_staff = True

    def test_searching_for_valid_order_number_redirects_to_order_page(self):
        # Importing here as the import makes DB queries
        from oscar.apps.dashboard.orders.forms import OrderSearchForm
        order = create_order()
        fields = OrderSearchForm.base_fields.keys()
        pairs = dict(zip(fields, ['']*len(fields)))
        pairs['order_number'] = order.number
        pairs['response_format'] = 'html'
        url = '%s?%s' % (reverse('dashboard:order-list'),
                         '&'.join(['%s=%s' % (k,v) for k,v in pairs.items()]))
        response = self.client.get(url)
        self.assertIsRedirect(response)


class PermissionBasedDashboardOrderTests(ClientTestCase):
    permissions = ['partner.dashboard_access', ]

    def setUp(self):
        """
        Two partners with one product each, and one user each.
        Three orders: order #1 for product #1, order #2 for product #2,
                      and order #3 for both products.
        """
        self.client = Client()
        self.user1 = self.create_user(username='user1@example.com')
        self.user2 = self.create_user(username='user2@example.com')
        self.partner1 = G(Partner, users=[self.user1])
        self.partner2 = G(Partner, users=[self.user2])
        self.product1 = create_product(partner=self.partner1)
        self.product2 = create_product(partner=self.partner2)
        self.basket1 = Basket.objects.create()
        self.basket2 = Basket.objects.create()
        self.basket12 = Basket.objects.create()
        self.basket1.add_product(self.product1)
        self.basket2.add_product(self.product2)
        self.basket12.add_product(self.product1)
        self.basket12.add_product(self.product2)
        self.address = G(ShippingAddress)
        self.order1 = create_order(basket=self.basket1,
                                   shipping_address=self.address)
        self.order2 = create_order(basket=self.basket2,
                                   shipping_address=self.address)
        self.order12 = create_order(basket=self.basket12,
                                    shipping_address=self.address)

    def test_staff_user_can_list_all_orders(self):
        self.is_staff = True
        self.login()
        orders = [self.order1, self.order2, self.order12]
        # order-list
        response = self.client.get(reverse('dashboard:order-list'))
        self.assertIsOk(response)
        self.assertEqual(set(response.context['orders']),
                         set(orders))
        # order-detail
        for order in orders:
            url = reverse('dashboard:order-detail',
                          kwargs={'number': order.number})
            self.assertIsOk(self.client.get(url))

    def test_non_staff_can_only_list_her_orders(self):
        # order-list user1
        self.client.login(username='user1@example.com', password=self.password)
        response = self.client.get(reverse('dashboard:order-list'))
        self.assertEqual(set(response.context['orders']),
                         set([self.order1]))
        # order-list user2
        self.client.login(username='user2@example.com', password=self.password)
        response = self.client.get(reverse('dashboard:order-list'))
        self.assertEqual(set(response.context['orders']),
                         set([self.order2]))
        # order-detail user2
        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.order2.number})
        self.assertIsOk(self.client.get(url))
        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.order12.number})
        self.assertNoAccess(self.client.get(url))
        # order-line-detail user2
        url = reverse('dashboard:order-line-detail',
                      kwargs={'number': self.order2.number,
                              'line_id': self.order2.lines.all()[0].pk})
        self.assertIsOk(self.client.get(url))
        url = reverse('dashboard:order-line-detail',
                      kwargs={'number': self.order12.number,
                              'line_id': self.order12.lines.all()[0].pk})
        self.assertNoAccess(self.client.get(url))
        # order-shipping-address
        url = reverse('dashboard:order-shipping-address',
                      kwargs={'number': self.order2.number})
        self.assertIsOk(self.client.get(url))
        url = reverse('dashboard:order-shipping-address',
                      kwargs={'number': self.order12.number})
        self.assertNoAccess(self.client.get(url))



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
