import csv

from django.db.models import get_model

from oscar.core.loading import get_class

ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ProductRecord = get_model('analytics', 'ProductRecord')
UserRecord = get_model('analytics', 'UserRecord')


class ProductReportGenerator(ReportGenerator):
    
    filename_template = 'product-analytics.csv'
    code = 'product_analytics'
    description = 'Product analytics'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['Product',
                      'Views',
                      'Basket additions',
                      'Purchases',]
        writer.writerow(header_row)
        
        records = ProductRecord._default_manager.all()
        for record in records:
            row = [record.product, record.num_views, record.num_basket_additions, record.num_purchases]
            writer.writerow(row)
            
    def is_available_to(self, user):
        return user.is_staff
    
    def filename(self):
        return self.filename_template
    

class UserReportGenerator(ReportGenerator):
    
    filename_template = 'user-analytics.csv'
    code = 'user_analytics'
    description = 'User analytics'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['Username',
                      'Name',
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
        
        records = UserRecord._default_manager.select_related().all()
        for record in records:
            row = [record.user.username, record.user.get_full_name(), record.user.date_joined, 
                   record.num_product_views, record.num_basket_additions, record.num_orders,
                   record.num_order_lines, record.num_order_items, record.total_spent, record.date_last_order]
            writer.writerow(row)
            
    def is_available_to(self, user):
        return user.is_staff
    
    def filename(self):
        return self.filename_template