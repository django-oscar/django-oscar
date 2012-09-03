from oscar.apps.checkout import views


class PaymentDetailsView(views.PaymentDetailsView):

    def handle_payment(self, order_number, total_incl_tax, **kwargs):
        # Create a payment event
        self.add_payment_event('Authorize', total_incl_tax)
