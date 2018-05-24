from decimal import Decimal as D

from django.utils.translation import gettext_lazy as _

from oscar.apps.order import exceptions
from oscar.core.loading import get_model

ShippingEventQuantity = get_model('order', 'ShippingEventQuantity')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')


class EventHandler(object):
    """
    Handle requested order events.

    This is an important class: it houses the core logic of your shop's order
    processing pipeline.
    """

    def __init__(self, user=None):
        self.user = user

    # Core API
    # --------

    def handle_shipping_event(self, order, event_type, lines,
                              line_quantities, **kwargs):
        """
        Handle a shipping event for a given order.

        This is most common entry point to this class - most of your order
        processing should be modelled around shipping events.  Shipping events
        can be used to trigger payment and communication events.

        You will generally want to override this method to implement the
        specifics of you order processing pipeline.
        """
        # Example implementation
        self.validate_shipping_event(
            order, event_type, lines, line_quantities, **kwargs)
        return self.create_shipping_event(
            order, event_type, lines, line_quantities, **kwargs)

    def handle_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        """
        Handle a payment event for a given order.

        These should normally be called as part of handling a shipping event.
        It is rare to call to this method directly.  It does make sense for
        refunds though where the payment event may be unrelated to a particular
        shipping event and doesn't directly correspond to a set of lines.
        """
        self.validate_payment_event(
            order, event_type, amount, lines, line_quantities, **kwargs)
        return self.create_payment_event(
            order, event_type, amount, lines, line_quantities, **kwargs)

    def handle_order_status_change(self, order, new_status, note_msg=None):
        """
        Handle a requested order status change

        This method is not normally called directly by client code.  The main
        use-case is when an order is cancelled, which in some ways could be
        viewed as a shipping event affecting all lines.
        """
        order.set_status(new_status)
        if note_msg:
            self.create_note(order, note_msg)

    # Validation methods
    # ------------------

    def validate_shipping_event(self, order, event_type, lines,
                                line_quantities, **kwargs):
        """
        Test if the requested shipping event is permitted.

        If not, raise InvalidShippingEvent
        """
        errors = []
        for line, qty in zip(lines, line_quantities):
            # The core logic should be in the model.  Ensure you override
            # 'is_shipping_event_permitted' and enforce the correct order of
            # shipping events.
            if not line.is_shipping_event_permitted(event_type, qty):
                msg = _("The selected quantity for line #%(line_id)s is too"
                        " large") % {'line_id': line.id}
                errors.append(msg)
        if errors:
            raise exceptions.InvalidShippingEvent(", ".join(errors))

    def validate_payment_event(self, order, event_type, amount, lines=None,
                               line_quantities=None, **kwargs):
        if lines and line_quantities:
            errors = []
            for line, qty in zip(lines, line_quantities):
                if not line.is_payment_event_permitted(event_type, qty):
                    msg = _("The selected quantity for line #%(line_id)s is too"
                            " large") % {'line_id': line.id}
                    errors.append(msg)
            if errors:
                raise exceptions.InvalidPaymentEvent(", ".join(errors))

    # Query methods
    # -------------
    # These are to help determine the status of lines

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

    # Payment stuff
    # -------------

    def calculate_payment_event_subtotal(self, event_type, lines,
                                         line_quantities):
        """
        Calculate the total charge for the passed event type, lines and line
        quantities.

        This takes into account the previous prices that have been charged for
        this event.

        Note that shipping is not including in this subtotal.  You need to
        subclass and extend this method if you want to include shipping costs.
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

    # Stock
    # -----

    def are_stock_allocations_available(self, lines, line_quantities):
        """
        Check whether stock records still have enough stock to honour the
        requested allocations.

        Lines whose product doesn't track stock are disregarded, which means
        this method will return True if only non-stock-tracking-lines are
        passed.
        This means you can just throw all order lines to this method, without
        checking whether stock tracking is enabled or not.
        This is okay, as calling consume_stock_allocations() has no effect for
        non-stock-tracking lines.
        """
        for line, qty in zip(lines, line_quantities):
            record = line.stockrecord
            if not record:
                return False
            if not record.can_track_allocations:
                continue
            if not record.is_allocation_consumption_possible(qty):
                return False
        return True

    def consume_stock_allocations(self, order, lines=None, line_quantities=None):
        """
        Consume the stock allocations for the passed lines.

        If no lines/quantities are passed, do it for all lines.
        """
        if not lines:
            lines = order.lines.all()
        if not line_quantities:
            line_quantities = [line.quantity for line in lines]
        for line, qty in zip(lines, line_quantities):
            if line.stockrecord:
                line.stockrecord.consume_allocation(qty)

    def cancel_stock_allocations(self, order, lines=None, line_quantities=None):
        """
        Cancel the stock allocations for the passed lines.

        If no lines/quantities are passed, do it for all lines.
        """
        if not lines:
            lines = order.lines.all()
        if not line_quantities:
            line_quantities = [line.quantity for line in lines]
        for line, qty in zip(lines, line_quantities):
            if line.stockrecord:
                line.stockrecord.cancel_allocation(qty)

    # Model instance creation
    # -----------------------

    def create_shipping_event(self, order, event_type, lines, line_quantities,
                              **kwargs):
        reference = kwargs.get('reference', '')
        event = order.shipping_events.create(
            event_type=event_type, notes=reference)
        try:
            for line, quantity in zip(lines, line_quantities):
                event.line_quantities.create(
                    line=line, quantity=quantity)
        except exceptions.InvalidShippingEvent:
            event.delete()
            raise
        return event

    def create_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        reference = kwargs.get('reference', "")
        event = order.payment_events.create(
            event_type=event_type, amount=amount, reference=reference)
        if lines and line_quantities:
            for line, quantity in zip(lines, line_quantities):
                event.line_quantities.create(
                    line=line, quantity=quantity)
        return event

    def create_communication_event(self, order, event_type):
        return order.communication_events.create(event_type=event_type)

    def create_note(self, order, message, note_type='System'):
        return order.notes.create(
            message=message, note_type=note_type, user=self.user)
