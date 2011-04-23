import csv

from oscar.core.loading import import_module
report_classes = import_module('reports.reports', ['ReportGenerator'])
analytics_models = import_module('analytics.models', ['ProductRecord', 'UserRecord'])


class ProductReportGenerator(report_classes.ReportGenerator):
    
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
        
        records = analytics_models.ProductRecord._default_manager.all()
        for record in records:
            row = [record.product, record.num_views, record.num_basket_additions, record.num_purchases]
            writer.writerow(row)
            
    def is_available_to(self, user):
        return user.is_staff
    
    def filename(self):
        return self.filename_template
    

class UserReportGenerator(report_classes.ReportGenerator):
    
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
        
        records = analytics_models.UserRecord._default_manager.select_related().all()
        for record in records:
            row = [record.user.username, record.user.get_full_name(), record.user.date_joined, 
                   record.num_product_views, record.num_basket_additions, record.num_orders,
                   record.num_order_lines, record.num_order_items, record.total_spent, record.date_last_order]
            writer.writerow(row)
            
    def is_available_to(self, user):
        return user.is_staff
    
    def filename(self):
        return self.filename_template