from datacash import models, facade, gateway
from oscar.apps.order import processing
from oscar.apps.payment import exceptions

from .models import PaymentEventType


class EventHandler(processing.EventHandler):

    def handle_shipping_event(self, order, event_type, lines,
                              line_quantities, **kwargs):
        self.validate_shipping_event(
            order, event_type, lines, line_quantities, **kwargs)

        payment_event = None
        if event_type.name == 'Shipped':
            # Take payment for order lines
            self.take_payment_for_lines(
                order, lines, line_quantities)
            self.consume_stock_allocations(
                order, lines, line_quantities)

        shipping_event = self.create_shipping_event(
            order, event_type, lines, line_quantities,
            reference=kwargs.get('reference', None))
        if payment_event:
            shipping_event.payment_events.add(payment_event)

    def take_payment_for_lines(self, order, lines, line_quantities):
        settle, __ = PaymentEventType.objects.get_or_create(
            name="Settle")
        amount = self.calculate_amount_to_settle(
            settle, order, lines, line_quantities)
        # Take payment with Datacash (using pre-auth txn)
        txn = self.get_datacash_preauth(order)

        f = facade.Facade()
        try:
            datacash_ref = f.fulfill_transaction(
                order.number, amount, txn.datacash_reference,
                txn.auth_code)
        except exceptions.PaymentError as e:
            self.create_note(order, "Attempt to settle %.2f failed: %s" % (
                amount, e))
            raise

        # Record message
        msg = "Payment of %.2f settled using reference '%s' from initial transaction"
        msg = msg % (amount, txn.datacash_reference)
        self.create_note(order, msg)

        # Update order source
        source = order.sources.get(source_type__name='Datacash')
        source.debit(amount, reference=datacash_ref)

        # Create payment event
        return self.create_payment_event(
            order, settle, amount, lines, line_quantities,
            reference=datacash_ref)

    def calculate_amount_to_settle(
            self, event_type, order, lines, line_quantities):
        amt = self.calculate_payment_event_subtotal(
            event_type, lines, line_quantities)
        num_payments = order.payment_events.filter(
            event_type=event_type).count()
        if num_payments == 0:
            # Include shipping charge in first payment
            amt += order.shipping_incl_tax
        return amt

    def get_datacash_preauth(self, order):
        """
        Return the (successful) pre-auth Datacash transaction for
        the passed order.
        """
        transactions = models.OrderTransaction.objects.filter(
            order_number=order.number, method=gateway.PRE, status=1)
        if transactions.count() == 0:
            raise exceptions.PaymentError(
                "Unable to take payment as no PRE-AUTH "
                "transaction found for this order")
        return transactions[0]
