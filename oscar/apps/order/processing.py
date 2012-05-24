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
        creating the event models themeselves.  You will generally want to
        override this method to implement the specifics of you order processing
        pipeline.
        """
        self.create_shipping_event(order, event_type, lines, line_quantities, **kwargs)

    def has_any_line_passed_shipping_event(self, order, lines, line_quantities, event_name):
        """
        Test whether any one of the lines passed has been through the event
        specified.
        """
        events = order.shipping_events.filter(event_type__name=event_name)
        remaining_qtys = [line.quantity - qty for line, qty in zip(lines, line_quantities)]
        spare_line_qtys = dict(zip([line.id for line in lines], remaining_qtys))
        for event in events:
            for line_qty in event.line_quantities.all():
                line_id = line_qty.line.id
                if line_id in spare_line_qtys:
                    spare_line_qtys[line_id] -= line_qty.quantity
        return any(map(lambda x: x<0, spare_line_qtys.values()))

    def have_lines_passed_shipping_event(self, order, lines, line_quantities, event_name):
        """
        Test whether the passed lines and quantities have been through the
        specified shipping event.  

        This is useful for validating if certain shipping events are allowed (ie
        you can't return something before it has shipped).
        """
        events = order.shipping_events.filter(event_type__name=event_name)
        required_line_qtys = dict(zip([line.id for line in lines], line_quantities))
        for event in events:
            for line_qty in event.line_quantities.all():
                line_id = line_qty.line.id
                if line_id in required_line_qtys:
                    required_line_qtys[line_id] -= line_qty.quantity
        return not any(map(lambda x: x>0, required_line_qtys.values()))

    def handle_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        """
        Handle a payment event for a given order.
        """
        self.create_payment_event(order, event_type, amount, lines, line_quantities, **kwargs)

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
