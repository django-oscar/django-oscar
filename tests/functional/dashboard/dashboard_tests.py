from decimal import Decimal as D

from django.core.urlresolvers import reverse

from oscar.core import prices
from oscar.apps.dashboard.views import IndexView
from oscar.test.testcases import WebTestCase
from oscar.test.factories import create_order


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
            self.assertTrue('Password' not in response.content.decode('utf8'))

    def test_includes_hourly_report_with_no_orders(self):
        report = IndexView().get_hourly_report()
        self.assertEqual(len(report), 3)
        for i, j in zip(sorted(report.keys()),
                ['max_revenue', 'order_total_hourly', 'y_range']):
            self.assertEqual(i, j)

        self.assertEqual(len(report['order_total_hourly']), 12)
        self.assertEqual(len(report['y_range']), 0)
        self.assertEqual(report['max_revenue'], 0)

    def test_includes_hourly_report_with_orders(self):
        create_order(total=prices.Price('GBP', excl_tax=D('34.05'),
                                        tax=D('0.00')))
        create_order(total=prices.Price('GBP', excl_tax=D('21.90'),
                                        tax=D('0.00')))
        report = IndexView().get_hourly_report()

        self.assertEqual(len(report['order_total_hourly']), 12)
        self.assertEqual(len(report['y_range']), 11)
        self.assertEqual(report['max_revenue'], D('60'))

    def test_has_stats_vars_in_context(self):
        response = self.get(reverse('dashboard:index'))

        self.assertInContext(response, 'total_orders_last_day')
        self.assertInContext(response, 'total_lines_last_day')
        self.assertInContext(response, 'average_order_costs')
        self.assertInContext(response, 'total_revenue_last_day')
        self.assertInContext(response, 'hourly_report_dict')

        self.assertInContext(response, 'total_products')
        self.assertInContext(response, 'total_open_stock_alerts')
        self.assertInContext(response, 'total_closed_stock_alerts')

        self.assertInContext(response, 'total_site_offers')
        self.assertInContext(response, 'total_vouchers')

        self.assertInContext(response, 'total_orders')
        self.assertInContext(response, 'total_lines')
        self.assertInContext(response, 'total_revenue')
        self.assertInContext(response, 'order_status_breakdown')
