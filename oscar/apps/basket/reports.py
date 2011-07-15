import csv
from oscar.apps.reports.reports import ReportGenerator

from oscar.core.loading import import_module
import_module('reports.reports', ['ReportGenerator'], locals())
import_module('basket.models', ['Basket', 'OPEN', 'SUBMITTED'], locals())


class OpenBasketReportGenerator(ReportGenerator):
    
    filename_template = 'open-baskets-%s-%s.csv'
    code = 'open_baskets'
    description = 'Open baskets'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['User ID',
                      'Username',
                      'Name',
                      'Email',
                      'Basket status',
                      'Num lines',
                      'Num items',
                      'Value',
                      'Date of creation',
                      'Time since creation',
                     ]
        writer.writerow(header_row)
        
        baskets = Basket._default_manager.filter(status=Basket.OPEN)
        for basket in baskets:
            if basket.owner:
                row = [basket.owner_id, basket.owner.username, basket.owner.get_full_name(). basket.owner.email,
                       basket.status, basket.num_lines,
                       basket.num_items, basket.total_incl_tax, 
                       basket.date_created, basket.time_since_creation]
            else:
                row = [basket.owner_id, None, None, None, basket.status, basket.num_lines,
                       basket.num_items, basket.total_incl_tax, 
                       basket.date_created, basket.time_since_creation]
            writer.writerow(row)


class SubmittedBasketReportGenerator(ReportGenerator):
    
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
        
        baskets = Basket._default_manager.filter(status=Basket.SUBMITTED)
        for basket in baskets:
            row = [basket.owner_id, basket.owner, basket.status, basket.num_lines,
                   basket.num_items, basket.total_incl_tax, 
                   basket.date_created, basket.time_before_submit]
            writer.writerow(row)
