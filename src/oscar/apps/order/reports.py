import datetime

from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class, get_model

ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class('dashboard.reports.reports',
                               'ReportCSVFormatter')
ReportHTMLFormatter = get_class('dashboard.reports.reports',
                                'ReportHTMLFormatter')
Order = get_model('order', 'Order')


class OrderReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'orders-%s-to-%s.csv'

    def generate_csv(self, response, orders):
        writer = self.get_csv_writer(response)
        header_row = [_('Order number'),
                      _('Name'),
                      _('Email'),
                      _('Total incl. tax'),
                      _('Date placed')]
        writer.writerow(header_row)
        for order in orders:
            row = [
                order.number,
                '-' if order.is_anonymous else order.user.get_full_name(),
                order.email,
                order.total_incl_tax,
                self.format_datetime(order.date_placed)]
            writer.writerow(row)

    def filename(self, **kwargs):
        return self.filename_template % (
            kwargs['start_date'], kwargs['end_date'])


class OrderReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'dashboard/reports/partials/order_report.html'


class OrderReportGenerator(ReportGenerator):
    code = 'order_report'
    description = _("Orders placed")
    date_range_field_name = 'date_placed'

    formatters = {
        'CSV_formatter': OrderReportCSVFormatter,
        'HTML_formatter': OrderReportHTMLFormatter,
    }

    def generate(self):
        qs = Order._default_manager.all()

        if self.start_date:
            qs = qs.filter(date_placed__gte=self.start_date)
        if self.end_date:
            qs = qs.filter(
                date_placed__lt=self.end_date + datetime.timedelta(days=1))

        additional_data = {
            'start_date': self.start_date,
            'end_date': self.end_date
        }

        return self.formatter.generate_response(qs, **additional_data)

    def is_available_to(self, user):
        return user.is_staff
