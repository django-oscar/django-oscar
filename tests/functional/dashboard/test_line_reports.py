from django.urls import reverse

from oscar.core.loading import get_class
from oscar.test.testcases import WebTestCase
from oscar.test.factories import OrderFactory, OrderLineFactory

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class OrderLineReportsDashboardTests(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get("analytics", "view_userrecord")

    def test_order_line_report_no_date_range(self):
        """Test order line report generation without date range"""
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.forms["generate_report_form"]["report_type"] = "order_line_report"
        response = response.forms["generate_report_form"].submit()
        self.assertIsOk(response)

    def test_order_line_report_with_date_range(self):
        """Test order line report generation with date range"""
        # Create test data
        order = OrderFactory()
        OrderLineFactory(order=order)
        
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.forms["generate_report_form"]["report_type"] = "order_line_report"
        response.forms["generate_report_form"]["date_from"] = "2017-01-01"
        response.forms["generate_report_form"]["date_to"] = "2017-12-31"
        response = response.forms["generate_report_form"].submit()
        self.assertIsOk(response)

    def test_order_line_report_csv_download(self):
        """Test order line report CSV download"""
        # Create test data
        order = OrderFactory()
        OrderLineFactory(order=order)
        
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.forms["generate_report_form"]["report_type"] = "order_line_report"
        response.forms["generate_report_form"]["date_from"] = "2017-01-01"
        response.forms["generate_report_form"]["date_to"] = "2017-12-31"
        response.forms["generate_report_form"]["download"] = "true"
        response = response.forms["generate_report_form"].submit()
        
        self.assertIsOk(response)
        # Should be a CSV file download
        self.assertEqual(response.content_type, "text/csv")
        
    def test_order_line_report_html_display(self):
        """Test order line report HTML display with data"""
        # Create test data
        order = OrderFactory(number="100001")
        line = OrderLineFactory(
            order=order,
            title="Test Product",
            quantity=2,
            partner_name="Test Partner"
        )
        
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.forms["generate_report_form"]["report_type"] = "order_line_report"
        response = response.forms["generate_report_form"].submit()
        
        self.assertIsOk(response)
        # Check that the data appears in the HTML
        self.assertContains(response, "100001")  # Order number
        self.assertContains(response, "Test Product")  # Product title
        self.assertContains(response, "Test Partner")  # Partner name

    def test_order_line_report_empty_results(self):
        """Test order line report with no matching results"""
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        # Use date range that won't match any orders
        response.forms["generate_report_form"]["report_type"] = "order_line_report"
        response.forms["generate_report_form"]["date_from"] = "2000-01-01"
        response.forms["generate_report_form"]["date_to"] = "2000-01-02"
        response = response.forms["generate_report_form"].submit()
        
        self.assertIsOk(response)
        # Should show "No results found"
        self.assertContains(response, "No results found")

    def test_order_line_report_access_permission(self):
        """Test that order line report generator correctly checks staff permission"""
        from oscar.apps.order.line_reports import OrderLineReportGenerator
        from oscar.core.loading import get_model
        User = get_model("myauth", "User")
        
        # Test with staff user (should have access)
        staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            password='test'
        )
        staff_user.is_staff = True
        staff_user.save()
        
        # Test with non-staff user (should not have access)
        non_staff_user = User.objects.create_user(
            username='non_staff_user',
            email='nonstaff@example.com',
            password='test'
        )
        
        generator = OrderLineReportGenerator()
        self.assertTrue(generator.is_available_to(staff_user))
        self.assertFalse(generator.is_available_to(non_staff_user))

    def test_order_line_report_columns_display(self):
        """Test that all required columns are displayed in HTML report"""
        # Create test data with all fields
        order = OrderFactory(number="100002")
        line = OrderLineFactory(
            order=order,
            title="Full Test Product",
            quantity=3,
            partner_sku="TEST-SKU-123",
            partner_name="Full Test Partner"
        )
        
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.forms["generate_report_form"]["report_type"] = "order_line_report"
        response = response.forms["generate_report_form"].submit()
        
        self.assertIsOk(response)
        
        # Check all expected column headers
        self.assertContains(response, "Order number")
        self.assertContains(response, "SKU") 
        self.assertContains(response, "Product title")
        self.assertContains(response, "Quantity")
        self.assertContains(response, "Line price (incl. tax)")
        self.assertContains(response, "Partner name")
        
        # Check that actual data appears
        self.assertContains(response, "100002")
        self.assertContains(response, "TEST-SKU-123")
        self.assertContains(response, "Full Test Product")
        self.assertContains(response, "3")  # quantity
        self.assertContains(response, "Full Test Partner")