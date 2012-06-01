import csv

from django.db.models import get_model

from oscar.core.loading import get_class
ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
Voucher = get_model('voucher', 'Voucher')


class VoucherReportGenerator(ReportGenerator):
    
    filename_template = 'voucher-performance.csv'
    code = 'vouchers'
    description = 'Voucher performance'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['Voucher code',
                      'Added to a basket',
                      'Used in an order',
                      'Total discount',
                     ]
        writer.writerow(header_row)
        
        vouchers = Voucher._default_manager.all()
        for voucher in vouchers:
            row = [voucher.code, voucher.num_basket_additions, voucher.num_orders, voucher.total_discount]
            writer.writerow(row)

    def filename(self):
        return self.filename_template
