from django.db.models.loading import get_model

ShippingEvent = get_model('order', 'ShippingEvent')
ShippingEventQuantity = get_model('order', 'ShippingEventQuantity')


class EventHandler(object):

    def handle_shipping_event(self, order, event_type, lines, line_quantities):
        """
        Handle a shipping event for a given order.

        This might involve taking payment, sending messages and 
        creating the event models themeselves.
        """
        self.create_shipping_event(order, event_type, lines, line_quantities)

    def create_shipping_event(self, order, event_type, lines, line_quantities):
        event = order.shipping_events.create(event_type=event_type)
        for line, quantity in zip(lines, line_quantities):
            ShippingEventQuantity.objects.create(event=event,
                                                 line=line,
                                                 quantity=quantity)
