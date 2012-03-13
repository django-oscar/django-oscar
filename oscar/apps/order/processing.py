from django.db.models.loading import get_model

from oscar.apps.order.exceptions import InvalidShippingEvent

ShippingEventQuantity = get_model('order', 'ShippingEventQuantity')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')


class EventHandler(object):

    def handle_order_status_change(self, order, new_status):
        """
        Handle a requested order status change
        """
        order.set_status(new_status)

    def handle_shipping_event(self, order, event_type, lines, line_quantities, **kwargs):
        """
        Handle a shipping event for a given order.

        This might involve taking payment, sending messages and 
        creating the event models themeselves.
        """
        self.create_shipping_event(order, event_type, lines, line_quantities, **kwargs)

    def handle_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        """
        Handle a payment event for a given order.
        """
        self.create_payment_event(order, event_type, amount, lines, line_quantities, **kwargs)

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
    
    def create_shipping_event(self, order, event_type, lines, line_quantities,
                              **kwargs):
        reference = kwargs.get('reference', None)
        event = order.shipping_events.create(event_type=event_type,
                                             notes=reference)
        try:
            for line, quantity in zip(lines, line_quantities):
                ShippingEventQuantity.objects.create(event=event,
                                                    line=line,
                                                    quantity=quantity)
        except InvalidShippingEvent:
            event.delete()
            raise

    def create_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        event = order.payment_events.create(event_type=event_type, amount=amount)
        if lines and line_quantities:
            for line, quantity in zip(lines, line_quantities):
                PaymentEventQuantity.objects.create(event=event,
                                                    line=line,
                                                    quantity=quantity)

    def create_communication_event(self, order, event_type):
        order.communication_events.create(event_type=event_type)

    def create_note(self, order, message, note_type='System'):
        order.notes.create(message=message, note_type=note_type)
