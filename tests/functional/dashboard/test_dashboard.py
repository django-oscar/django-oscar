from decimal import Decimal as D

from django.urls import reverse

from oscar.apps.dashboard.views import IndexView
from oscar.apps.order.models import Order
from oscar.core import prices
from oscar.core.loading import get_model
from oscar.test.factories import (
    UserFactory,
    create_basket,
    create_order,
    create_product,
)
from oscar.test.testcases import WebTestCase

StockAlert = get_model("partner", "StockAlert")


GENERIC_STATS_KEYS = (
    "total_orders_last_day",
    "total_lines_last_day",
    "average_order_costs",
    "total_revenue_last_day",
    "hourly_report_dict",
    "total_customers_last_day",
    "total_open_baskets_last_day",
    "total_products",
    "total_open_stock_alerts",
    "total_closed_stock_alerts",
    "total_customers",
    "total_open_baskets",
    "total_orders",
    "total_lines",
    "total_revenue",
    "order_status_breakdown",
)
STAFF_STATS_KEYS = (
    "offer_maps",
    "total_vouchers",
)


class TestDashboardIndexForAnonUser(WebTestCase):
    is_anonymous = True

    def test_is_not_available(self):
        response = self.get(reverse("dashboard:index")).follow()
        self.assertContains(response, "username", status_code=200)


class TestDashboardIndexForStaffUser(WebTestCase):
    is_staff = True

    def test_is_available(self):
        urls = (
            "dashboard:index",
            "dashboard:order-list",
            "dashboard:users-index",
        )
        for name in urls:
            response = self.get(reverse(name))
            self.assertContains(response, "Welcome")

    def test_includes_hourly_report_with_no_orders(self):
        report = IndexView().get_hourly_report(Order.objects.all())
        self.assertEqual(len(report), 3)

        keys = ["max_revenue", "order_total_hourly", "y_range"]
        for i, j in zip(sorted(report.keys()), keys):
            self.assertEqual(i, j)

        self.assertEqual(len(report["order_total_hourly"]), 12)
        self.assertEqual(len(report["y_range"]), 0)
        self.assertEqual(report["max_revenue"], 0)

    def test_includes_hourly_report_with_orders(self):
        create_order(total=prices.Price("GBP", excl_tax=D("34.05"), tax=D("0.00")))
        create_order(total=prices.Price("GBP", excl_tax=D("21.90"), tax=D("0.00")))
        report = IndexView().get_hourly_report(Order.objects.all())

        self.assertEqual(len(report["order_total_hourly"]), 12)
        self.assertEqual(len(report["y_range"]), 11)
        self.assertEqual(report["max_revenue"], D("60"))

    def test_has_stats_vars_in_context(self):
        response = self.get(reverse("dashboard:index"))
        for key in GENERIC_STATS_KEYS + STAFF_STATS_KEYS:
            self.assertInContext(response, key)

    def test_login_redirects_to_dashboard_index(self):
        page = self.get(reverse("dashboard:login"))
        form = page.forms["dashboard_login_form"]
        form["username"] = self.email
        form["password"] = self.password
        response = form.submit("login_submit")
        self.assertRedirectsTo(response, "dashboard:index")


class TestDashboardIndexForPartnerUser(WebTestCase):
    permissions = ["partner.dashboard_access"]

    def test_is_available(self):
        urls = ("dashboard:index", "dashboard:order-list")
        for name in urls:
            response = self.get(reverse(name))
            self.assertContains(response, "Welcome")

    def test_is_not_available(self):
        urls = (
            "dashboard:users-index",
            "dashboard:partner-list",
            "dashboard:partner-create",
            "dashboard:offer-list",
            "dashboard:reports-index",
        )
        for name in urls:
            response = self.get(reverse(name), expect_errors=True)
            self.assertContains(response, "Permission denied!", status_code=403)

    def test_stats(self):
        response = self.get(reverse("dashboard:index"))
        for key in GENERIC_STATS_KEYS:
            self.assertInContext(response, key)
        for key in STAFF_STATS_KEYS:
            self.assertNotInContext(response, key)


class TestDashboardIndexStatsForNonStaffUser(WebTestCase):
    permissions = ["partner.dashboard_access"]

    def setUp(self):
        super().setUp()
        customer = UserFactory()
        product1 = create_product(partner_name="Partner 1", price=D(5))
        product2 = create_product(partner_name="Partner 2", price=D(10))
        create_product(partner_name="Partner 2", price=D(15))
        basket1 = create_basket(empty=True)
        basket1.add_product(product1)
        create_order(basket=basket1, user=customer)
        basket2 = create_basket(empty=True)
        basket2.add_product(product1)
        basket2 = create_basket(empty=True)
        basket2.add_product(product2)
        for i in range(9):
            create_order(basket=basket2, user=customer, number="1000%s" % i)
        stockrecord1 = product1.stockrecords.first()
        stockrecord2 = product2.stockrecords.first()
        self.partner1 = stockrecord1.partner
        self.partner2 = stockrecord2.partner
        StockAlert.objects.create(stockrecord=stockrecord1, threshold=10)
        StockAlert.objects.create(stockrecord=stockrecord2, threshold=5)

    def test_partner1(self):
        user = self.create_user(username="user", email="testuser@example.com")
        self.partner1.users.add(self.user)
        self.partner2.users.add(user)
        response = self.get(reverse("dashboard:index"))
        context = response.context
        self.assertEqual(context["total_orders_last_day"], 1)
        self.assertEqual(context["total_lines_last_day"], 1)
        self.assertEqual(context["total_revenue_last_day"], D(27))
        self.assertEqual(context["total_customers_last_day"], 1)
        self.assertEqual(context["total_open_baskets_last_day"], 1)
        self.assertEqual(context["total_products"], 1)
        self.assertEqual(context["total_open_stock_alerts"], 1)
        self.assertEqual(context["total_closed_stock_alerts"], 0)
        self.assertEqual(context["total_customers"], 1)
        self.assertEqual(context["total_open_baskets"], 1)
        self.assertEqual(context["total_orders"], 1)
        self.assertEqual(context["total_lines"], 1)
        self.assertEqual(context["total_revenue"], D(27))

    def test_partner2(self):
        user = self.create_user(username="user", email="testuser@example.com")
        self.partner1.users.add(user)
        self.partner2.users.add(self.user)
        response = self.get(reverse("dashboard:index"))
        context = response.context
        self.assertEqual(context["total_orders_last_day"], 9)
        self.assertEqual(context["total_lines_last_day"], 9)
        self.assertEqual(context["total_revenue_last_day"], D(288))
        self.assertEqual(context["total_customers_last_day"], 1)
        self.assertEqual(context["total_open_baskets_last_day"], 0)
        self.assertEqual(context["total_products"], 2)
        self.assertEqual(context["total_open_stock_alerts"], 1)
        self.assertEqual(context["total_closed_stock_alerts"], 0)
        self.assertEqual(context["total_customers"], 1)
        self.assertEqual(context["total_open_baskets"], 0)
        self.assertEqual(context["total_orders"], 9)
        self.assertEqual(context["total_lines"], 9)
        self.assertEqual(context["total_revenue"], D(288))
