import csv

from oscar.core.loading import import_module
import_module('reports.reports', ['ReportGenerator'], locals())
import_module('offer.models', ['ConditionalOffer'], locals())


class OfferReportGenerator(ReportGenerator):
    
    filename_template = 'conditional-offer-performance.csv'
    code = 'conditional-offers'
    description = 'Offer performance'
    
    def generate(self, response):
        writer = csv.writer(response)
        header_row = ['Offer',
                      'Total discount',
                     ]
        writer.writerow(header_row)
        
        for offer in ConditionalOffer._default_manager.all():
            row = [offer, offer.total_discount]
            writer.writerow(row)

    def filename(self):
        return self.filename_template