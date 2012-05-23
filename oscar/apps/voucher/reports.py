import csv

from oscar.core.loading import import_module
import_module('dashboard.reports.reports', ['ReportGenerator'], locals())
import_module('dashboard.reports.reports', ['ReportCSVFormatter'], locals())
import_module('dashboard.reports.reports', ['ReportHTMLFormatter'], locals())
import_module('voucher.models', ['Voucher'], locals())


class VoucherReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'voucher-performance.csv'

    def generate_csv(self, response, vouchers):
        writer = csv.writer(response)
        header_row = ['Voucher code',
                      'Added to a basket',
                      'Used in an order',
                      'Total discount',
                     ]
        writer.writerow(header_row)

        for voucher in vouchers:
            row = [voucher.code,
                   voucher.num_basket_additions,
                   voucher.num_orders,
                   voucher.total_discount]
            writer.writerow(row)


class VoucherReportHTMLFormatter(ReportHTMLFormatter):
    template = 'dashboard/reports/partials/voucher_report.html'


class VoucherReportGenerator(ReportGenerator):

    code = 'vouchers'
    description = 'Voucher performance'

    formatters = {
        'CSV_formatter': VoucherReportCSVFormatter,
        'HTML_formatter': VoucherReportHTMLFormatter
    }

    def generate(self):
        vouchers = Voucher._default_manager.all()
        return self.formatter.generate_response(vouchers)
