import csv

from django.db.models import get_model

from oscar.core.loading import get_class
ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


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