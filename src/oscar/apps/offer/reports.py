from decimal import Decimal as D

from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

ReportGenerator = get_class('dashboard.reports.reports', 'ReportGenerator')
ReportCSVFormatter = get_class('dashboard.reports.reports',
                               'ReportCSVFormatter')
ReportHTMLFormatter = get_class('dashboard.reports.reports',
                                'ReportHTMLFormatter')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
OrderDiscount = get_model('order', 'OrderDiscount')


class OfferReportCSVFormatter(ReportCSVFormatter):
    filename_template = 'conditional-offer-performance.csv'

    def generate_csv(self, response, offers):
        writer = self.get_csv_writer(response)
        header_row = [_('Offer'),
                      _('Total discount')
                      ]
        writer.writerow(header_row)

        for offer in offers:
            row = [offer, offer['total_discount']]
            writer.writerow(row)


class OfferReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = 'oscar/dashboard/reports/partials/offer_report.html'


class OfferReportGenerator(ReportGenerator):
    code = 'conditional-offers'
    description = _('Offer performance')
    model_class = OrderDiscount

    formatters = {
        'CSV_formatter': OfferReportCSVFormatter,
        'HTML_formatter': OfferReportHTMLFormatter,
    }

    def generate(self):
        offer_discounts = {}
        for discount in self.queryset:
            if discount.offer_id not in offer_discounts:
                try:
                    all_offers = ConditionalOffer._default_manager
                    offer = all_offers.get(id=discount.offer_id)
                except ConditionalOffer.DoesNotExist:
                    continue
                offer_discounts[discount.offer_id] = {
                    'offer': offer,
                    'total_discount': D('0.00')
                }
            offer_discounts[discount.offer_id]['total_discount'] \
                += discount.amount

        return self.formatter.generate_response(list(offer_discounts.values()))
