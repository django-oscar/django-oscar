import csv

from django.db.models import get_model

from oscar.core.loading import get_class
ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
Order = get_model('order', 'Order')


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
            row = [order.number,
                   order.user,
                   order.total_incl_tax,
                   self.format_datetime(order.date_placed)]
            writer.writerow(row)
            
    def is_available_to(self, user):
        return user.is_staff and user.has_perm('order.can_view')