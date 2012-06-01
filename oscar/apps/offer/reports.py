import csv
from decimal import Decimal as D

from django.db.models import get_model

from oscar.core.loading import get_class
ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class('dashboard.reports.reports', 'ReportCSVFormatter')
ReportHTMLFormatter = get_class('dashboard.reports.reports', 'ReportHTMLFormatter')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
OrderDiscount = get_model('order', 'OrderDiscount')


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
        discounts = OrderDiscount._default_manager.filter(
            order__date_placed__gte=self.start_date,
            order__date_placed__lt=self.end_date
        )
        offer_discounts = {}
        for discount in discounts:
            if discount.offer_id not in offer_discounts:
                try:
                    offer = ConditionalOffer._default_manager.get(id=discount.offer_id)
                except ConditionalOffer.DoesNotExist:
                    continue
                offer_discounts[discount.offer_id] = {
                    'offer': offer,
                    'total_discount': D('0.00')
                }
            offer_discounts[discount.offer_id]['total_discount'] += discount.amount

        return self.formatter.generate_response(offer_discounts.values())
