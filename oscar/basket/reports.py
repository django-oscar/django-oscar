import csv

from oscar.services import import_module
report_classes = import_module('reports.reports', ['ReportGenerator'])
basket_models = import_module('basket.models', ['Basket', 'OPEN', 'SUBMITTED'])


class OpenBasketReportGenerator(report_classes.ReportGenerator):
    
    filename_template = 'open-baskets-%s-%s.csv'
    code = 'open_baskets'
    description = 'Open baskets'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['User ID',
                      'User',
                      'Basket status',
                      'Num lines',
                      'Num items',
                      'Value',
                      'Date of creation',
                      'Time since creation',
                     ]
        writer.writerow(header_row)
        
        baskets = basket_models.Basket._default_manager.filter(status=basket_models.OPEN)
        for basket in baskets:
            row = [basket.owner_id, basket.owner, basket.status, basket.num_lines,
                   basket.num_items, basket.total_incl_tax, 
                   basket.date_created, basket.time_since_creation]
            writer.writerow(row)


class SubmittedBasketReportGenerator(report_classes.ReportGenerator):
    
    filename_template = 'submitted_baskets-%s-%s.csv'
    code = 'submitted_baskets'
    description = 'Submitted baskets'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['User ID',
                      'User',
                      'Basket status',
                      'Num lines',
                      'Num items',
                      'Value',
                      'Time between creation and submission',
                     ]
        writer.writerow(header_row)
        
        baskets = basket_models.Basket._default_manager.filter(status=basket_models.SUBMITTED)
        for basket in baskets:
            row = [basket.owner_id, basket.owner, basket.status, basket.num_lines,
                   basket.num_items, basket.total_incl_tax, 
                   basket.date_created, basket.time_before_submit]
            writer.writerow(row)
