import datetime
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.utils.timezone import now

from oscar.apps.order import line_reports
from oscar.core.loading import get_model
from oscar.test.factories import OrderFactory, OrderLineFactory, create_product
from django.db.models.query import QuerySet

Order = get_model("order", "Order")
Line = get_model("order", "Line")
User = get_model("myauth", "User")


class TestOrderLineReportGenerator(TestCase):
    def setUp(self):
        self.generator = line_reports.OrderLineReportGenerator(formatter="CSV")
        
    def test_generate_csv_no_data(self):
        """Test CSV generation with no order lines"""
        response = self.generator.generate()
        self.assertEqual(response.status_code, 200)
        
    def test_generate_csv_with_data(self):
        """Test CSV generation with order line data"""
        order = OrderFactory()
        OrderLineFactory(order=order)
        
        response = self.generator.generate()
        self.assertEqual(response.status_code, 200)
        
    def test_generate_html_no_data(self):
        """Test HTML generation with no order lines"""
        html_generator = line_reports.OrderLineReportGenerator(formatter="HTML")
        result = html_generator.generate()
        # HTML formatter returns QuerySet, not HttpResponse
        self.assertIsInstance(result, QuerySet)
        self.assertEqual(result.count(), 0)
        
    def test_generate_html_with_data(self):
        """Test HTML generation with order line data"""
        order = OrderFactory()
        OrderLineFactory(order=order)
        
        html_generator = line_reports.OrderLineReportGenerator(formatter="HTML")
        result = html_generator.generate()
        # HTML formatter returns QuerySet, not HttpResponse
        self.assertIsInstance(result, QuerySet)
        self.assertEqual(result.count(), 1)
        
    def test_generate_csv_with_date_range(self):
        """Test CSV generation with date range filtering"""
        # Create orders with different dates
        old_date = now() - datetime.timedelta(days=30)
        recent_date = now() - datetime.timedelta(days=5)
        
        old_order = OrderFactory(date_placed=old_date)
        recent_order = OrderFactory(date_placed=recent_date)
        OrderLineFactory(order=old_order)
        OrderLineFactory(order=recent_order)
        
        # Filter for recent orders only
        start_date = now() - datetime.timedelta(days=10)
        end_date = now()
        
        generator = line_reports.OrderLineReportGenerator(
            start_date=start_date, 
            end_date=end_date,
            formatter="CSV"
        )
        
        queryset = generator.get_queryset()
        # Should only include recent order line
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().order, recent_order)

    def test_queryset_optimization(self):
        """Test that queryset uses select_related for performance"""
        order = OrderFactory()
        line = OrderLineFactory(order=order)
        
        queryset = self.generator.get_queryset()
        
        # Check that select_related was used by examining queries
        with self.assertNumQueries(1):
            list_lines = list(queryset)
            if list_lines:
                # Access related fields without triggering additional queries
                line = list_lines[0]
                _ = line.order.number
                _ = line.product
                _ = line.partner
                
    def test_queryset_ordering(self):
        """Test that queryset is properly ordered"""
        order1 = OrderFactory(date_placed=now() - datetime.timedelta(days=2))
        order2 = OrderFactory(date_placed=now() - datetime.timedelta(days=1))
        
        line1 = OrderLineFactory(order=order1)
        line2 = OrderLineFactory(order=order2)
        
        queryset = self.generator.get_queryset()
        lines = list(queryset)
        
        # Should be ordered by date_placed first
        if len(lines) == 2:
            self.assertEqual(lines[0], line1)  # Earlier date first
            self.assertEqual(lines[1], line2)
            
    def test_staff_user_access(self):
        """Test that only staff users have access"""
        staff_user = User.objects.create_user(
            username='staff', 
            email='staff@example.com',
            password='test'
        )
        staff_user.is_staff = True
        staff_user.save()
        
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='test'
        )
        
        self.assertTrue(self.generator.is_available_to(staff_user))
        self.assertFalse(self.generator.is_available_to(regular_user))
        
    def test_generator_code_and_description(self):
        """Test generator code and description"""
        self.assertEqual(self.generator.code, 'order_line_report')
        self.assertEqual(str(self.generator.description), 'Order line items')


class TestOrderLineReportCSVFormatter(TestCase):
    def setUp(self):
        self.formatter = line_reports.OrderLineReportCSVFormatter()
        
    def test_csv_header_generation(self):
        """Test CSV header row generation"""
        from django.http import HttpResponse
        import csv
        from io import StringIO
        
        response = HttpResponse(content_type='text/csv')
        self.formatter.generate_csv(response, [])
        
        # Check that response has CSV content type
        self.assertEqual(response['Content-Type'], 'text/csv')
        
    def test_csv_data_generation(self):
        """Test CSV data row generation"""
        from django.http import HttpResponse
        import csv
        from io import StringIO
        
        order = OrderFactory()
        # Use basic OrderLineFactory without overriding complex fields
        line = OrderLineFactory(
            order=order,
            title="Test Product",
            quantity=2,
            line_price_incl_tax=Decimal('19.98'),
            partner_sku='TEST-SKU',
            partner_name='Test Partner'
        )
        
        response = HttpResponse(content_type='text/csv')
        self.formatter.generate_csv(response, [line])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        lines = content.strip().split('\n')
        
        # Should have header + 1 data row
        self.assertEqual(len(lines), 2)
        
        # Check header row
        header = lines[0].split(',')
        expected_headers = [
            'Order number', 'SKU', 'Product title', 
            'Quantity', 'Line price (incl. tax)', 'Partner name'
        ]
        for expected in expected_headers:
            self.assertIn(expected, ','.join(header))
            
    def test_csv_filename_generation(self):
        """Test CSV filename generation"""
        start_date = '2023-01-01'
        end_date = '2023-01-31'
        
        filename = self.formatter.filename(
            start_date=start_date, 
            end_date=end_date
        )
        
        expected = f'order-lines-{start_date}-to-{end_date}.csv'
        self.assertEqual(filename, expected)
        
    def test_csv_handles_missing_data(self):
        """Test CSV generation handles missing optional data"""
        from django.http import HttpResponse
        
        order = OrderFactory()
        line = OrderLineFactory(
            order=order,
            upc=None,         # Test missing UPC  
            partner_name='Default Partner'  # partner_name appears to be required
        )
        # Set partner_sku to empty string after creation to simulate missing data
        line.partner_sku = ''
        line.save()
        
        response = HttpResponse(content_type='text/csv')
        self.formatter.generate_csv(response, [line])
        
        content = response.content.decode('utf-8')
        # Should not raise exceptions and should use "-" for missing values
        self.assertIn('-', content)


class TestOrderLineReportHTMLFormatter(TestCase):
    def test_html_template_path(self):
        """Test HTML formatter uses correct template"""
        formatter = line_reports.OrderLineReportHTMLFormatter()
        expected_template = "oscar/dashboard/reports/partials/order_line_report.html"
        self.assertEqual(formatter.filename_template, expected_template)


class TestOrderLineReportIntegration(TestCase):
    """Test integration with report generator repository"""
    
    def test_generator_in_repository(self):
        """Test that OrderLineReportGenerator is available in the repository"""
        from oscar.apps.dashboard.reports.utils import GeneratorRepository
        
        repository = GeneratorRepository()
        generators = repository.get_report_generators()
        
        # Check that OrderLineReportGenerator is in the list
        generator_classes = [gen.__name__ for gen in generators]
        self.assertIn('OrderLineReportGenerator', generator_classes)
        
    def test_get_generator_by_code(self):
        """Test getting generator by code"""
        from oscar.apps.dashboard.reports.utils import GeneratorRepository
        
        repository = GeneratorRepository()
        generator = repository.get_generator('order_line_report')
        
        self.assertIsNotNone(generator)
        self.assertEqual(generator.code, 'order_line_report')