import csv

from oscar.services import import_module
report_classes = import_module('reports.reports', ['ReportGenerator'])
analytics_models = import_module('analytics.models', ['ProductRecord'])


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