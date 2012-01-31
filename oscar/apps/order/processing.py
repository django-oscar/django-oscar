from django.db.models.loading import get_model

ShippingEventQuantity = get_model('order', 'ShippingEventQuantity')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')


class EventHandler(object):

    def handle_shipping_event(self, order, event_type, lines, line_quantities):
        """
        Handle a shipping event for a given order.

        This might involve taking payment, sending messages and 
        creating the event models themeselves.
        """
        self.create_shipping_event(order, event_type, lines, line_quantities)

    def handle_payment_event(self, order, event_type, lines, line_quantities):
        """
        Handle a payment event for a given order.
        """
        self.create_payment_event(order, event_type, lines, line_quantities)

    def create_shipping_event(self, order, event_type, lines, line_quantities):
        event = order.shipping_events.create(event_type=event_type)
        for line, quantity in zip(lines, line_quantities):
            ShippingEventQuantity.objects.create(event=event,
                                                 line=line,
                                                 quantity=quantity)

    def create_payment_event(self, order, event_type, lines, line_quantities):
        event = order.payment_events.create(event_type=event_type)
        for line, quantity in zip(lines, line_quantities):
            PaymentEventQuantity.objects.create(event=event,
                                                line=line,
                                                quantity=quantity)

    def create_communication_event(self, order, event_type):
        order.communication_events.create(event_type=event_type)

    def create_note(self, order, message, note_type='System'):
        order.notes.create(message=message)
