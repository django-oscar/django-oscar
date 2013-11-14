from decimal import Decimal as D

from django.core.urlresolvers import reverse

from oscar.core import prices
from oscar.apps.dashboard.views import IndexView
from oscar.test.testcases import ClientTestCase
from oscar.test.factories import create_order


class TestDashboardIndexForAnonUser(ClientTestCase):
    is_anonymous = True

    def test_is_not_available(self):
        response = self.client.get(reverse('dashboard:index'), follow=True)
        self.assertContains(response, 'login-username', status_code=200)


class TestDashboardIndexForStaffUser(ClientTestCase):
    is_staff = True

    def test_is_available(self):
        urls = ('dashboard:index',
                'dashboard:order-list',
                'dashboard:users-index',)
        for name in urls:
            response = self.client.get(reverse(name))
            self.assertTrue('Password' not in response.content)

    def test_includes_hourly_report_with_no_orders(self):
        report = IndexView().get_hourly_report()
        self.assertItemsEqual(report, ['order_total_hourly', 'max_revenue',
                                       'y_range'])
        self.assertEquals(len(report['order_total_hourly']), 12)
        self.assertEquals(len(report['y_range']), 0)
        self.assertEquals(report['max_revenue'], 0)

    def test_includes_hourly_report_with_orders(self):
        create_order(total=prices.Price('GBP', excl_tax=D('34.05'),
                                        tax=D('0.00')))
        create_order(total=prices.Price('GBP', excl_tax=D('21.90'),
                                        tax=D('0.00')))
        report = IndexView().get_hourly_report()

        self.assertEquals(len(report['order_total_hourly']), 12)
        self.assertEquals(len(report['y_range']), 11)
        self.assertEquals(report['max_revenue'], D('60'))

    def test_has_stats_vars_in_context(self):
        response = self.client.get(reverse('dashboard:index'))

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
