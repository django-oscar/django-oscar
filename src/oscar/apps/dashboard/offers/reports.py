from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class

ReportCSVFormatter = get_class("dashboard.reports.reports", "ReportCSVFormatter")


class OrderDiscountCSVFormatter(ReportCSVFormatter):
    filename_template = "order-discounts-for-offer-%s.csv"

    def generate_csv(self, response, order_discounts):
        writer = self.get_csv_writer(response)
        header_row = [_("Order number"), _("Order date"), _("Order total"), _("Cost")]
        writer.writerow(header_row)
        for order_discount in order_discounts:
            order = order_discount.order
            row = [
                order.number,
                self.format_datetime(order.date_placed),
                order.total_incl_tax,
                order_discount.amount,
            ]
            writer.writerow(row)

    def filename(self, offer):
        return self.filename_template % offer.id
