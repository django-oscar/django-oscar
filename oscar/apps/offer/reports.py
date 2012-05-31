import csv

from django.db.models import get_model

from oscar.core.loading import get_class
ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class('dashboard.reports.reports', 'ReportCSVFormatter')
ReportHTMLFormatter = get_class('dashboard.reports.reports', 'ReportHTMLFormatter')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


class OfferReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'conditional-offer-performance.csv'

    def generate_csv(self, response, offers):
        writer = csv.writer(response)
        header_row = ['Offer',
                      'Total discount',
                     ]
        writer.writerow(header_row)

        for offer in offers:
            row = [offer, offer.total_discount]
            writer.writerow(row)


class OfferReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'dashboard/reports/partials/offer_report.html'



class OfferReportGenerator(ReportGenerator):

    code = 'conditional-offers'
    description = 'Offer performance'

    formatters = {
        'CSV_formatter': OfferReportCSVFormatter,
        'HTML_formatter': OfferReportHTMLFormatter,
    }

    def generate(self):
        offers = ConditionalOffer._default_manager.all()
        return self.formatter.generate_response(offers)
