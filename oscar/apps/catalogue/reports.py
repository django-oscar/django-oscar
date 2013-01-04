from oscar.core.reports import Report
from oscar.core.reports import Generator
from oscar.core.reports.formatters import HTMLFormatter
from oscar.core.reports.formatters import CSVFormatter

from oscar.apps.catalogue.models import Product


class ProductReport(Report):
    """
    Report that shows all the available products in the system
    """
    def get_data(self, params=None):
        return Product.objects.all()


class ProductReportHTMLFormatter(HTMLFormatter):
    template_name = 'dashboard/reports/catalogue/product.html'


class ProductReportHTMLGenerator(Generator):
    """
    HTML Report Generator
    """
    report_class = ProductReport
    formatter_class = ProductReportHTMLFormatter
    title = 'Product HTML Report'


class ProductReportCSVFormatter(CSVFormatter):
    fields = [
        'upc',
        'title',
        'status',
        'product_class'
    ]


class ProductReportCSVGenerator(Generator):
    """
    CSV Report Generator
    """
    report_class = ProductReport
    formatter_class = ProductReportCSVFormatter
    title = 'Product CSV Report'

