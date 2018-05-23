from decimal import Decimal as D

from django.urls import reverse

from oscar.core import prices
from oscar.apps.dashboard.views import IndexView
from oscar.apps.order.models import Order
from oscar.test.testcases import WebTestCase
from oscar.test.factories import create_order


GENERIC_STATS_KEYS = (
    'total_orders_last_day',
    'total_lines_last_day',
    'average_order_costs',
    'total_revenue_last_day',
    'hourly_report_dict',
    'total_customers_last_day',
    'total_open_baskets_last_day',
    'total_products',
    'total_open_stock_alerts',
    'total_closed_stock_alerts',
    'total_customers',
    'total_open_baskets',
    'total_orders',
    'total_lines',
    'total_revenue',
    'order_status_breakdown',
)
STAFF_STATS_KEYS = (
    'total_site_offers',
    'total_vouchers',
    'total_promotions',
)


class TestDashboardIndexForAnonUser(WebTestCase):
    is_anonymous = True

    def test_is_not_available(self):
        response = self.get(reverse('dashboard:index')).follow()
        self.assertContains(response, 'username', status_code=200)


class TestDashboardIndexForStaffUser(WebTestCase):
    is_staff = True

    def test_is_available(self):
        urls = ('dashboard:index',
                'dashboard:order-list',
                'dashboard:users-index',)
        for name in urls:
            response = self.get(reverse(name))
            self.assertContains(response, 'Welcome')

    def test_includes_hourly_report_with_no_orders(self):
        report = IndexView().get_hourly_report(Order.objects.all())
        self.assertEqual(len(report), 3)

        keys = ['max_revenue', 'order_total_hourly', 'y_range']
        for i, j in zip(sorted(report.keys()), keys):
            self.assertEqual(i, j)

        self.assertEqual(len(report['order_total_hourly']), 12)
        self.assertEqual(len(report['y_range']), 0)
        self.assertEqual(report['max_revenue'], 0)

    def test_includes_hourly_report_with_orders(self):
        create_order(total=prices.Price('GBP', excl_tax=D('34.05'),
                                        tax=D('0.00')))
        create_order(total=prices.Price('GBP', excl_tax=D('21.90'),
                                        tax=D('0.00')))
        report = IndexView().get_hourly_report(Order.objects.all())

        self.assertEqual(len(report['order_total_hourly']), 12)
        self.assertEqual(len(report['y_range']), 11)
        self.assertEqual(report['max_revenue'], D('60'))

    def test_has_stats_vars_in_context(self):
        response = self.get(reverse('dashboard:index'))
        for key in GENERIC_STATS_KEYS + STAFF_STATS_KEYS:
            self.assertInContext(response, key)


class TestDashboardIndexForPartnerUser(WebTestCase):
    permissions = ['partner.dashboard_access']

    def test_is_available(self):
        urls = ('dashboard:index', 'dashboard:order-list')
        for name in urls:
            response = self.get(reverse(name))
            self.assertContains(response, 'Welcome')

    def test_is_not_available(self):
        urls = ('dashboard:users-index',
                'dashboard:partner-list',
                'dashboard:partner-create',
                'dashboard:offer-list',
                'dashboard:reports-index')
        for name in urls:
            response = self.get(reverse(name), expect_errors=True)
            self.assertContains(response, 'Permission denied!',
                                status_code=403)

    def test_stats(self):
        response = self.get(reverse('dashboard:index'))
        for key in GENERIC_STATS_KEYS:
            self.assertInContext(response, key)
        for key in STAFF_STATS_KEYS:
            self.assertNotInContext(response, key)
