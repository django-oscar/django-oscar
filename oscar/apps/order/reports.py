import csv

from oscar.core.loading import import_module
import_module('reports.reports', ['ReportGenerator'], locals())
import_module('order.models', ['Order'], locals())


class OrderReportGenerator(ReportGenerator):
    
    filename_template = 'orders-%s-to-%s.csv'
    code = 'order_report'
    description = "Orders placed"
    
    def generate(self, response):
        orders = Order._default_manager.filter(
            date_placed__gte=self.start_date
        ).filter(date_placed__lt=self.end_date)
        
        writer = csv.writer(response)
        header_row = ['Order number',
                      'User',
                      'Total incl. tax',
                      'Date placed',]
        writer.writerow(header_row)
        for order in orders:
            row = [order.number, order.user, order.total_incl_tax, order.date_placed]
            writer.writerow(row)
            
    def is_available_to(self, user):
        return user.is_staff and user.has_perm('order.can_view')