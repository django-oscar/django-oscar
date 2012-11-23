from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class

ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class(
    'dashboard.reports.reports', 'ReportCSVFormatter')
ReportHTMLFormatter = get_class(
    'dashboard.reports.reports', 'ReportHTMLFormatter')
Voucher = get_model('voucher', 'Voucher')


class VoucherReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'voucher-performance.csv'

    def generate_csv(self, response, vouchers):
        writer = self.get_csv_writer(response)
        header_row = [_('Voucher code'),
                      _('Added to a basket'),
                      _('Used in an order'),
                      _('Total discount')]
        writer.writerow(header_row)

        for voucher in vouchers:
            row = [voucher.code,
                   voucher.num_basket_additions,
                   voucher.num_orders,
                   voucher.total_discount]
            writer.writerow(row)


class VoucherReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'dashboard/reports/partials/voucher_report.html'


class VoucherReportGenerator(ReportGenerator):

    code = 'vouchers'
    description = _('Voucher performance')

    formatters = {
        'CSV_formatter': VoucherReportCSVFormatter,
        'HTML_formatter': VoucherReportHTMLFormatter}

    def generate(self):
        vouchers = Voucher._default_manager.all()
        return self.formatter.generate_response(vouchers)
