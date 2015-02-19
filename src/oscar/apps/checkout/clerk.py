# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from oscar.core.loading import get_class, get_model

OrderCreator = get_class('order.utils', 'OrderCreator')
OrderNumberGenerator = get_class('order.utils', 'OrderNumberGenerator')
OrderTotalCalculator = get_class('checkout.calculators',
                                 'OrderTotalCalculator')
NoShippingRequired = get_class('shipping.methods', 'NoShippingRequired')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')
PaymentEventType = get_model('order', 'PaymentEventType')
PaymentEvent = get_model('order', 'PaymentEvent')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')
post_checkout = get_class('checkout.signals', 'post_checkout')


class Clerk(object):
    """
    The clerk can place an order when given a basket and other additional
    information.
    """

    _order_number = None
    _shipping_method = None
    shipping_address = None
    billing_address = None
    _order_status = None
    guest_email = None

    def __init__(self, user, basket):
        self.user = user
        self.basket = basket
        self.payment_sources = []
        self.payment_events = []

    @property
    def shipping_charge(self):
        return self.shipping_method.calculate(self.basket)

    @property
    def order_total(self):
        # Taxes must be known at this point
        assert self.basket.is_tax_known, (
            "Basket tax must be set before a user can place an order")
        assert self.shipping_charge.is_tax_known, (
            "Shipping charge tax must be set before a user can place an order")

        return OrderTotalCalculator().calculate(self.basket,
                                                self.shipping_charge)

    @property
    def order_number(self):
        if not self._order_number:
            self._order_number = (
                OrderNumberGenerator().order_number(self.basket))

        return self._order_number

    @order_number.setter
    def order_number(self, value):
        self._order_number = value

    @property
    def order_status(self):
        if not self._order_status:
            self._order_status = self.get_initial_order_status()

        return self._order_status

    @order_status.setter
    def order_status(self, value):
        self._order_status = value

    @property
    def shipping_method(self):
        if not self._shipping_method:
            if not self.basket.is_shipping_required():
                self._shipping_method = NoShippingRequired()

        return self._shipping_method

    @shipping_method.setter
    def shipping_method(self, value):
        self._shipping_method = value

    def receive_payment(self, payment_sources, payment_events):
        for source in payment_sources:
            source_type, __ = SourceType.objects.get_or_create(
                code=source.type_code,
                defaults={'name': source.type_name})

            self.payment_sources.append(
                Source(source_type=source_type,
                       currency=source.currency,
                       amount_allocated=source.amount_allocated,
                       amount_debited=source.amount_debited,
                       reference=source.reference))

        for event in payment_events:
            event_type, __ = PaymentEventType.objects.get_or_create(
                name=event.type_name)
            event = PaymentEvent(
                event_type=event_type, amount=event.amount,
                reference=event.reference)

            self.payment_events.append(event)

    def place_order(self, **kwargs):
        self.save_shipping_address()
        self.save_billing_address()

        if self.guest_email:
            kwargs['guest_email'] = self.guest_email

        order = OrderCreator().place_order(
            basket=self.basket,
            total=self.order_total,
            user=self.user,
            order_number=self.order_number,
            shipping_address=self.shipping_address,
            shipping_method=self.shipping_method,
            shipping_charge=self.shipping_charge,
            billing_address=self.billing_address,
            status=self.order_status, **kwargs)

        self.save_payment_sources(order)
        self.save_payment_events(order)

        if self.user.is_authenticated() and self.shipping_address:
            self.user.handle_order_shipped_to(self.shipping_address)

        self.basket.submit()

        post_checkout.send(sender=self, order=order)

        return order

    def save_billing_address(self):
        if self.billing_address:
            self.billing_address.save()

    def save_shipping_address(self):
        if self.shipping_address:
            self.shipping_address.save()

    def save_payment_events(self, order):
        for event in self.payment_events:
            event.order = order
            event.save()

        if self.payment_events:
            # We assume all lines are involved in the initial payment event
            for line in order.lines.all():
                PaymentEventQuantity.objects.create(
                    event=event, line=line, quantity=line.quantity)

    def save_payment_sources(self, order):
        for source in self.payment_sources:
            source.order = order
            source.save()

    def get_initial_order_status(self):
        return None
