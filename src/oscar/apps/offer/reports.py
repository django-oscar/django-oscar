from django.db.models import OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

ReportGenerator = get_class("dashboard.reports.reports", "ReportGenerator")
ReportCSVFormatter = get_class("dashboard.reports.reports", "ReportCSVFormatter")
ReportHTMLFormatter = get_class("dashboard.reports.reports", "ReportHTMLFormatter")
ConditionalOffer = get_model("offer", "ConditionalOffer")
OrderDiscount = get_model("order", "OrderDiscount")


class OfferReportCSVFormatter(ReportCSVFormatter):
    filename_template = "conditional-offer-performance.csv"

    def generate_csv(self, response, offer_discounts):
        writer = self.get_csv_writer(response)
        header_row = [_("Offer"), _("Total discount")]
        writer.writerow(header_row)

        for discount in offer_discounts:
            writer.writerow(
                [discount["display_offer_name"], discount["total_discount"]]
            )


class OfferReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = "oscar/dashboard/reports/partials/offer_report.html"


class OfferReportGenerator(ReportGenerator):
    code = "conditional-offers"
    description = _("Offer performance")
    model_class = OrderDiscount

    formatters = {
        "CSV_formatter": OfferReportCSVFormatter,
        "HTML_formatter": OfferReportHTMLFormatter,
    }

    def get_queryset(self):
        offers = ConditionalOffer.objects.filter(pk=OuterRef("offer_id"))
        return (
            super()
            .get_queryset()
            .order_by()
            .values("offer_id")
            .annotate(
                total_discount=Sum("amount"),
                # Used to add a link to the offer in the report template, if the offer still exists.
                offer=Subquery(offers.values("pk")[:1]),
                # Find the name of the attached offer if it exists, otherwise the offer_name on a matching OrderDiscount
                # This is used to display the most appropriate name in the report template.
                display_offer_name=Coalesce(
                    Subquery(offers.values("name")[:1]),
                    Subquery(
                        OrderDiscount.objects.filter(pk=OuterRef("pk")).values(
                            "offer_name"
                        )[:1]
                    ),
                ),
            )
            .values("offer_id", "offer", "total_discount", "display_offer_name")
            .order_by("-total_discount")
        )
