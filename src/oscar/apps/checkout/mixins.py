import logging

from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse

from oscar.apps.checkout.signals import post_checkout
from oscar.core.loading import get_class, get_model

OrderCreator = get_class('order.utils', 'OrderCreator')
Dispatcher = get_class('customer.utils', 'Dispatcher')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')
BillingAddress = get_model('order', 'BillingAddress')
ShippingAddress = get_model('order', 'ShippingAddress')
OrderNumberGenerator = get_class('order.utils', 'OrderNumberGenerator')
PaymentEventType = get_model('order', 'PaymentEventType')
PaymentEvent = get_model('order', 'PaymentEvent')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')
UserAddress = get_model('address', 'UserAddress')
Basket = get_model('basket', 'Basket')
CommunicationEventType = get_model('customer', 'CommunicationEventType')

# Standard logger for checkout events
logger = logging.getLogger('oscar.checkout')


class OrderPlacementMixin(CheckoutSessionMixin):
    """
    Mixin which provides functionality for placing orders.

    Any view class which needs to place an order should use this mixin.
    """
    # Any payment sources should be added to this list as part of the
    # handle_payment method.  If the order is placed successfully, then
    # they will be persisted. We need to have the order instance before the
    # payment sources can be saved.
    _payment_sources = None

    # Any payment events should be added to this list as part of the
    # handle_payment method.
    _payment_events = None

    # Default code for the email to send after successful checkout
    communication_type_code = 'ORDER_PLACED'

    view_signal = post_checkout

    # Payment handling methods
    # ------------------------

    def handle_payment(self, order_number, total, **kwargs):
        """
        Handle any payment processing and record payment sources and events.

        This method is designed to be overridden within your project.  The
        default is to do nothing as payment is domain-specific.

        This method is responsible for handling payment and recording the
        payment sources (using the add_payment_source method) and payment
        events (using add_payment_event) so they can be
        linked to the order when it is saved later on.
        """
        pass

    def add_payment_source(self, source):
        """
        Record a payment source for this order
        """
        if self._payment_sources is None:
            self._payment_sources = []
        self._payment_sources.append(source)

    def add_payment_event(self, event_type_name, amount, reference=''):
        """
        Record a payment event for creation once the order is placed
        """
        event_type, __ = PaymentEventType.objects.get_or_create(
            name=event_type_name)
        # We keep a local cache of (unsaved) payment events
        if self._payment_events is None:
            self._payment_events = []
        event = PaymentEvent(
            event_type=event_type, amount=amount,
            reference=reference)
        self._payment_events.append(event)

    # Placing order methods
    # ---------------------

    def generate_order_number(self, basket):
        """
        Return a new order number
        """
        return OrderNumberGenerator().order_number(basket)

    def handle_order_placement(self, order_number, user, basket,
                               shipping_address, shipping_method,
                               shipping_charge, billing_address, order_total,
                               **kwargs):
        """
        Write out the order models and return the appropriate HTTP response

        We deliberately pass the basket in here as the one tied to the request
        isn't necessarily the correct one to use in placing the order.  This
        can happen when a basket gets frozen.
        """
        order = self.place_order(
            order_number=order_number, user=user, basket=basket,
            shipping_address=shipping_address, shipping_method=shipping_method,
            shipping_charge=shipping_charge, order_total=order_total,
            billing_address=billing_address, **kwargs)
        basket.submit()
        return self.handle_successful_order(order)

    def place_order(self, order_number, user, basket, shipping_address,
                    shipping_method, shipping_charge, order_total,
                    billing_address=None, **kwargs):
        """
        Writes the order out to the DB including the payment models
        """
        # Create saved shipping address instance from passed in unsaved
        # instance
        shipping_address = self.create_shipping_address(user, shipping_address)

        # We pass the kwargs as they often include the billing address form
        # which will be needed to save a billing address.
        billing_address = self.create_billing_address(
            user, billing_address, shipping_address, **kwargs)

        if 'status' not in kwargs:
            status = self.get_initial_order_status(basket)
        else:
            status = kwargs.pop('status')

        if 'request' not in kwargs:
            request = getattr(self, 'request', None)
        else:
            request = kwargs.pop('request')

        order = OrderCreator().place_order(
            user=user,
            order_number=order_number,
            basket=basket,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            shipping_charge=shipping_charge,
            total=order_total,
            billing_address=billing_address,
            status=status,
            request=request,
            **kwargs)
        self.save_payment_details(order)
        return order

    def create_shipping_address(self, user, shipping_address):
        """
        Create and return the shipping address for the current order.

        Compared to self.get_shipping_address(), ShippingAddress is saved and
        makes sure that appropriate UserAddress exists.
        """
        # For an order that only contains items that don't require shipping we
        # won't have a shipping address, so we have to check for it.
        if not shipping_address:
            return None
        shipping_address.save()
        if user.is_authenticated:
            self.update_address_book(user, shipping_address)
        return shipping_address

    def update_address_book(self, user, addr):
        """
        Update the user's address book based on the new shipping address
        """
        try:
            user_addr = user.addresses.get(
                hash=addr.generate_hash())
        except ObjectDoesNotExist:
            # Create a new user address
            user_addr = UserAddress(user=user)
            addr.populate_alternative_model(user_addr)
        if isinstance(addr, ShippingAddress):
            user_addr.num_orders_as_shipping_address += 1
        if isinstance(addr, BillingAddress):
            user_addr.num_orders_as_billing_address += 1
        user_addr.save()

    def create_billing_address(self, user, billing_address=None,
                               shipping_address=None, **kwargs):
        """
        Saves any relevant billing data (e.g. a billing address).
        """
        if not billing_address:
            return None
        billing_address.save()
        if user.is_authenticated:
            self.update_address_book(user, billing_address)
        return billing_address

    def save_payment_details(self, order):
        """
        Saves all payment-related details. This could include a billing
        address, payment sources and any order payment events.
        """
        self.save_payment_events(order)
        self.save_payment_sources(order)

    def save_payment_events(self, order):
        """
        Saves any relevant payment events for this order
        """
        if not self._payment_events:
            return
        for event in self._payment_events:
            event.order = order
            event.save()
            for line in order.lines.all():
                PaymentEventQuantity.objects.create(
                    event=event, line=line, quantity=line.quantity)

    def save_payment_sources(self, order):
        """
        Saves any payment sources used in this order.

        When the payment sources are created, the order model does not exist
        and so they need to have it set before saving.
        """
        if not self._payment_sources:
            return
        for source in self._payment_sources:
            source.order = order
            source.save()

    def get_initial_order_status(self, basket):
        return None

    # Post-order methods
    # ------------------

    def handle_successful_order(self, order):
        """
        Handle the various steps required after an order has been successfully
        placed.

        Override this view if you want to perform custom actions when an
        order is submitted.
        """
        # Send confirmation message (normally an email)
        self.send_confirmation_message(order, self.communication_type_code)

        # Flush all session data
        self.checkout_session.flush()

        # Save order id in session so thank-you page can load it
        self.request.session['checkout_order_id'] = order.id

        response = HttpResponseRedirect(self.get_success_url())
        self.send_signal(self.request, response, order)
        return response

    def send_signal(self, request, response, order):
        self.view_signal.send(
            sender=self, order=order, user=request.user,
            request=request, response=response)

    def get_success_url(self):
        return reverse('checkout:thank-you')

    def send_confirmation_message(self, order, code, **kwargs):
        try:
            ctx = self.get_message_context(order, code)
        except TypeError:
            # It seems like the get_message_context method was overridden and
            # it does not support the code argument yet
            logger.warning(
                'The signature of the get_message_context method has changed, '
                'please update it in your codebase'
            )
            ctx = self.get_message_context(order)

        try:
            event_type = CommunicationEventType.objects.get(code=code)
        except CommunicationEventType.DoesNotExist:
            # No event-type in database, attempt to find templates for this
            # type and render them immediately to get the messages.  Since we
            # have not CommunicationEventType to link to, we can't create a
            # CommunicationEvent instance.
            messages = CommunicationEventType.objects.get_and_render(code, ctx)
            event_type = None
        else:
            messages = event_type.get_messages(ctx)

        if messages and messages['body']:
            logger.info("Order #%s - sending %s messages", order.number, code)
            dispatcher = Dispatcher(logger)
            dispatcher.dispatch_order_messages(order, messages,
                                               event_type, **kwargs)
        else:
            logger.warning("Order #%s - no %s communication event type",
                           order.number, code)

    def get_message_context(self, order, code=None):
        ctx = {
            'user': self.request.user,
            'order': order,
            'site': get_current_site(self.request),
            'lines': order.lines.all()
        }

        # Attempt to add the order status URL to the email template ctx.
        try:
            if self.request.user.is_authenticated:
                path = reverse('customer:order',
                               kwargs={'order_number': order.number})
            else:
                path = reverse('customer:anon-order',
                               kwargs={'order_number': order.number,
                                       'hash': order.verification_hash()})
        except NoReverseMatch:
            # We don't care that much if we can't resolve the URL
            pass
        else:
            site = Site.objects.get_current()
            ctx['status_url'] = 'http://%s%s' % (site.domain, path)
        return ctx

    # Basket helpers
    # --------------

    def get_submitted_basket(self):
        basket_id = self.checkout_session.get_submitted_basket_id()
        return Basket._default_manager.get(pk=basket_id)

    def freeze_basket(self, basket):
        """
        Freeze the basket so it can no longer be modified
        """
        # We freeze the basket to prevent it being modified once the payment
        # process has started.  If your payment fails, then the basket will
        # need to be "unfrozen".  We also store the basket ID in the session
        # so the it can be retrieved by multistage checkout processes.
        basket.freeze()

    def restore_frozen_basket(self):
        """
        Restores a frozen basket as the sole OPEN basket.  Note that this also
        merges in any new products that have been added to a basket that has
        been created while payment.
        """
        try:
            fzn_basket = self.get_submitted_basket()
        except Basket.DoesNotExist:
            # Strange place.  The previous basket stored in the session does
            # not exist.
            pass
        else:
            fzn_basket.thaw()
            if self.request.basket.id != fzn_basket.id:
                fzn_basket.merge(self.request.basket)
                # Use same strategy as current request basket
                fzn_basket.strategy = self.request.basket.strategy
                self.request.basket = fzn_basket
