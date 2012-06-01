import csv

from django.db.models import get_model

from oscar.core.loading import get_class
ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class('dashboard.reports.reports', 'ReportCSVFormatter')
ReportHTMLFormatter = get_class('dashboard.reports.reports', 'ReportHTMLFormatter')
Order = get_model('order', 'Order')


class OrderReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'orders-%s-to-%s.csv'

    def generate_csv(self, response, orders):
        writer = csv.writer(response)
        header_row = ['Order number',
                      'User',
                      'Total incl. tax',
                      'Date placed',]
        writer.writerow(header_row)
        for order in orders:
            row = [order.number,
                   order.user,
                   order.total_incl_tax,
                   self.format_datetime(order.date_placed)]
            writer.writerow(row)

    def filename(self, **kwargs):
        return self.filename_template % (kwargs['start_date'], kwargs['end_date'])


class OrderReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'dashboard/reports/partials/order_report.html'


class OrderReportGenerator(ReportGenerator):

    code = 'order_report'
    description = "Orders placed"

    formatters = {
        'CSV_formatter': OrderReportCSVFormatter,
        'HTML_formatter': OrderReportHTMLFormatter,
    }

    def generate(self):
        orders = Order._default_manager.filter(
            date_placed__gte=self.start_date
        ).filter(date_placed__lt=self.end_date)

        additional_data = {
            'start_date': self.start_date,
            'end_date': self.end_date
        }

        return self.formatter.generate_response(orders, **additional_data)

    def is_available_to(self, user):
        return user.is_staff and user.has_perm('order.can_view')
