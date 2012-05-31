import csv

from django.db.models import get_model
from django.template.defaultfilters import date

from oscar.core.loading import get_class

ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class('dashboard.reports.reports', 'ReportCSVFormatter')
ReportHTMLFormatter = get_class('dashboard.reports.reports', 'ReportHTMLFormatter')
ProductRecord = get_model('analytics', 'ProductRecord')
UserRecord = get_model('analytics', 'UserRecord')


class ProductReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'conditional-offer-performance.csv'

    def generate_csv(self, response, products):
        writer = csv.writer(response)
        header_row = ['Product',
                      'Views',
                      'Basket additions',
                      'Purchases',]
        writer.writerow(header_row)

        for record in products:
            row = [record.product,
                   record.num_views,
                   record.num_basket_additions,
                   record.num_purchases]
            writer.writerow(row)


class ProductReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'dashboard/reports/partials/product_report.html'


class ProductReportGenerator(ReportGenerator):

    code = 'product_analytics'
    description = 'Product analytics'

    formatters = {
      'CSV_formatter': ProductReportCSVFormatter,
      'HTML_formatter': ProductReportHTMLFormatter
    }

    def generate(self):
        records = ProductRecord._default_manager.all()
        return self.formatter.generate_response(records)

    def is_available_to(self, user):
        return user.is_staff


class UserReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'user-analytics.csv'

    def generate_csv(self, response, users):
        writer = csv.writer(response)
        header_row = ['Name',
                      'Date registered',
                      'Product views',
                      'Basket additions',
                      'Orders',
                      'Order lines',
                      'Order items',
                      'Total spent',
                      'Date of last order',
                      ]
        writer.writerow(header_row)

        for record in users:
            row = [record.user.get_full_name(),
                   self.format_date(record.user.date_joined),
                   record.num_product_views,
                   record.num_basket_additions,
                   record.num_orders,
                   record.num_order_lines,
                   record.num_order_items,
                   record.total_spent,
                   self.format_datetime(record.date_last_order)]
            writer.writerow(row)


class UserReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'dashboard/reports/partials/user_report.html'


class UserReportGenerator(ReportGenerator):

    code = 'user_analytics'
    description = 'User analytics'

    formatters = {
        'CSV_formatter': UserReportCSVFormatter,
        'HTML_formatter': UserReportHTMLFormatter
    }

    def generate(self):
        users = UserRecord._default_manager.select_related().all()
        return self.formatter.generate_response(users)

    def is_available_to(self, user):
        return user.is_staff
