from decimal import Decimal as D

from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _

from oscar.apps.order import exceptions

ShippingEventQuantity = get_model('order', 'ShippingEventQuantity')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')


class EventHandler(object):
    """
    Handle requested order events.

    This is an important class: it houses the core logic of your shop's order
    processing pipeline.
    """

    # Core API
    # --------

    def handle_shipping_event(self, order, event_type, lines,
                              line_quantities, **kwargs):
        """
        Handle a shipping event for a given order.

        This is most common entry point to this class - most of your order
        processing should be modelled around shipping events.

        This might involve taking payment, sending messages and
        creating the event models themeselves.  You will generally want to
        override this method to implement the specifics of you order processing
        pipeline.
        """
        self.validate_shipping_event(
            order, event_type, lines, line_quantities, **kwargs)
        self.create_shipping_event(
            order, event_type, lines, line_quantities, **kwargs)

    def handle_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        """
        Handle a payment event for a given order.
        """
        self.create_payment_event(order, event_type, amount, lines,
                                  line_quantities, **kwargs)

    def handle_order_status_change(self, order, new_status):
        """
        Handle a requested order status change
        """
        order.set_status(new_status)

    # Validation methods
    # ------------------

    def validate_shipping_event(self, order, event_type, lines,
                                line_quantities, **kwargs):
        """
        Test if the requested shipping event is permitted.

        If not, raise InvalidShippingEvent
        """
        self.validate_shipping_event_quantities(
            order, event_type, lines, line_quantities, **kwargs)

    def validate_shipping_event_quantities(
            self, order, event_type, lines, line_quantities, **kwargs):
        """
        Test if the proposed quantities of the event are valid
        """
        errors = []
        for line, qty in zip(lines, line_quantities):
            if not line.is_shipping_event_permitted(event_type, qty):
                msg = _("The selected quantity for line #%(line_id)s is too large") % {
                    'line_id': line.id}
                errors.append(msg)
        if errors:
            raise exceptions.InvalidShippingEvent(", ".join(errors))

    # Query methods
    # -------------
    # These are to help determine the status of lines

    def calculate_payment_event_subtotal(self, event_type, lines,
                                         line_quantities):
        """
        Calculate the total charge for the passed event type, lines and line
        quantities.

        This takes into account the previous prices that have been charged for
        this event.
        """
        total = D('0.00')
        for line, qty_to_consume in zip(lines, line_quantities):
            # This part is quite fiddly.  We need to skip the prices that have
            # already been settled.  This involves keeping a load of counters.

            # Count how many of this line have already been involved in an
            # event of this type.
            qty_to_skip = line.payment_event_quantity(event_type)

            # Test if request is sensible
            if qty_to_skip + qty_to_consume > line.quantity:
                raise exceptions.InvalidPaymentEvent

            # Consume prices in order of ID (this is the default but it's
            # better to be explicit)
            qty_consumed = 0
            for price in line.prices.all().order_by('id'):
                if qty_consumed == qty_to_consume:
                    # We've accounted for the asked-for quantity: we're done
                    break

                qty_available = price.quantity - qty_to_skip
                if qty_available <= 0:
                    # Skip the whole quantity of this price instance
                    qty_to_skip -= price.quantity
                else:
                    # Need to account for some of this price instance and
                    # track how many we needed to skip and how many we settled
                    # for.
                    qty_to_include = min(
                        qty_to_consume - qty_consumed, qty_available)
                    total += qty_to_include * price.price_incl_tax
                    # There can't be any left to skip if we've included some in
                    # our total
                    qty_to_skip = 0
                    qty_consumed += qty_to_include
        return total

    def have_lines_passed_shipping_event(self, order, lines, line_quantities,
                                         event_type):
        """
        Test whether the passed lines and quantities have been through the
        specified shipping event.

        This is useful for validating if certain shipping events are allowed
        (ie you can't return something before it has shipped).
        """
        for line, line_qty in zip(lines, line_quantities):
            if line.shipping_event_quantity(event_type) < line_qty:
                return False
        return True

    # Stock stuff

    def are_stock_allocations_available(self, lines, line_quantities):
        """
        Check whether stock records still have enough stock to honour the
        requested allocations.
        """
        for line, qty in zip(lines, line_quantities):
            record = line.product.stockrecord
            if not record.is_allocation_consumption_possible(qty):
                return False
        return True

    def consume_stock_allocations(self, order, lines, line_quantities):
        """
        Consume the stock allocations for the passed lines
        """
        for line, qty in zip(lines, line_quantities):
            if line.product:
                line.product.stockrecord.consume_allocation(qty)

    def cancel_stock_allocations(self, order, lines, line_quantities):
        """
        Cancel the stock allocations for the passed lines
        """
        for line, qty in zip(lines, line_quantities):
            line.product.stockrecord.cancel_allocation(qty)

    # Create event instances

    def create_shipping_event(self, order, event_type, lines, line_quantities,
                              **kwargs):
        reference = kwargs.get('reference', None)
        event = order.shipping_events.create(
            event_type=event_type, notes=reference)
        try:
            for line, quantity in zip(lines, line_quantities):
                event.line_quantities.create(
                    line=line, quantity=quantity)
        except exceptions.InvalidShippingEvent:
            event.delete()
            raise

    def create_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        event = order.payment_events.create(
            event_type=event_type, amount=amount)
        if lines and line_quantities:
            for line, quantity in zip(lines, line_quantities):
                PaymentEventQuantity.objects.create(
                    event=event, line=line, quantity=quantity)

    def create_communication_event(self, order, event_type):
        order.communication_events.create(event_type=event_type)

    def create_note(self, order, message, note_type='System'):
        order.notes.create(message=message, note_type=note_type)
