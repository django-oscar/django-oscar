import logging

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import get_model

from oscar.core.loading import get_class
OrderCreator = get_class('order.utils', 'OrderCreator')
Dispatcher = get_class('customer.utils', 'Dispatcher')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')

ShippingAddress = get_model('order', 'ShippingAddress')
CommunicationEvent = get_model('order', 'CommunicationEvent')
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
    """
    # Any payment sources should be added to this list as part of the
    # _handle_payment method.  If the order is placed successfully, then
    # they will be persisted.
    _payment_sources = None

    _payment_events = None

    # Default code for the email to send after successful checkout
    communication_type_code = 'ORDER_PLACED'

    def handle_order_placement(self, order_number, basket, total_incl_tax,
                               total_excl_tax, user=None, **kwargs):
        """
        Write out the order models and return the appropriate HTTP response

        We deliberately pass the basket in here as the one tied to the request
        isn't necessarily the correct one to use in placing the order.  This
        can happen when a basket gets frozen.
        """
        order = self.place_order(order_number, basket, total_incl_tax,
                                 total_excl_tax, user, **kwargs)
        basket.set_as_submitted()
        return self.handle_successful_order(order)

    def add_payment_source(self, source):
        if self._payment_sources is None:
            self._payment_sources = []
        self._payment_sources.append(source)

    def add_payment_event(self, event_type_name, amount):
        event_type, __ = PaymentEventType.objects.get_or_create(
            name=event_type_name)
        if self._payment_events is None:
            self._payment_events = []
        event = PaymentEvent(event_type=event_type, amount=amount)
        self._payment_events.append(event)

    def handle_successful_order(self, order):
        """
        Handle the various steps required after an order has been successfully
        placed.

        Override this view if you want to perform custom actions when an
        order is submitted.
        """
        # Send confirmation message (normally an email)
        self.send_confirmation_message(order)

        # Flush all session data
        self.checkout_session.flush()

        # Save order id in session so thank-you page can load it
        self.request.session['checkout_order_id'] = order.id

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('checkout:thank-you')

    def place_order(self, order_number, basket, total_incl_tax,
                    total_excl_tax, user=None, **kwargs):
        """
        Writes the order out to the DB including the payment models
        """
        shipping_address = self.create_shipping_address(basket)
        shipping_method = self.get_shipping_method(basket)
        billing_address = self.create_billing_address(shipping_address)

        if 'status' not in kwargs:
            status = self.get_initial_order_status(basket)
        else:
            status = kwargs.pop('status')

        # We allow a user to be passed in to handle cases where the order is
        # being placed on behalf of someone else.
        if user is None:
            user = self.request.user

        # Set guest email address for anon checkout.   Some libraries (eg
        # PayPal) will pass this explicitly so we take care not to clobber.
        if (not self.request.user.is_authenticated() and 'guest_email'
            not in kwargs):
            kwargs['guest_email'] = self.checkout_session.get_guest_email()

        order = OrderCreator().place_order(basket=basket,
                                           total_incl_tax=total_incl_tax,
                                           total_excl_tax=total_excl_tax,
                                           user=user,
                                           shipping_method=shipping_method,
                                           shipping_address=shipping_address,
                                           billing_address=billing_address,
                                           order_number=order_number,
                                           status=status,
                                           **kwargs)
        self.save_payment_details(order)
        return order

    def create_shipping_address(self, basket=None):
        """
        Create and returns the shipping address for the current order.

        If the shipping address was entered manually, then we simply
        write out a ShippingAddress model with the appropriate form data.  If
        the user is authenticated, then we create a UserAddress from this data
        too so it can be re-used in the future.

        If the shipping address was selected from the user's address book,
        then we convert the UserAddress to a ShippingAddress.
        """
        if not basket:
            basket = self.request.basket
        if not basket.is_shipping_required():
            return None

        addr_data = self.checkout_session.new_shipping_address_fields()
        addr_id = self.checkout_session.user_address_id()
        if addr_data:
            addr = self.create_shipping_address_from_form_fields(addr_data)
            self.create_user_address(addr_data)
        elif addr_id:
            addr = self.create_shipping_address_from_user_address(addr_id)
        else:
            raise AttributeError("No shipping address data found")
        return addr

    def create_shipping_address_from_form_fields(self, addr_data):
        """Creates a shipping address model from the saved form fields"""
        shipping_addr = ShippingAddress(**addr_data)
        shipping_addr.save()
        return shipping_addr

    def create_user_address(self, addr_data):
        """
        For signed-in users, we create a user address model which will go
        into their address book.
        """
        if self.request.user.is_authenticated():
            addr_data['user_id'] = self.request.user.id
            user_addr = UserAddress(**addr_data)
            # Check that this address isn't already in the db as we don't want
            # to fill up the customer address book with duplicate addresses
            try:
                UserAddress._default_manager.get(
                    hash=user_addr.generate_hash())
            except ObjectDoesNotExist:
                user_addr.save()

    def create_shipping_address_from_user_address(self, addr_id):
        """Creates a shipping address from a user address"""
        address = UserAddress._default_manager.get(pk=addr_id)
        # Increment the number of orders to help determine popularity of orders
        address.num_orders += 1
        address.save()

        shipping_addr = ShippingAddress()
        address.populate_alternative_model(shipping_addr)
        shipping_addr.save()
        return shipping_addr

    def create_billing_address(self, shipping_address=None):
        """
        Saves any relevant billing data (eg a billing address).
        """
        return None

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
        # We assume all lines are involved in the initial payment event
        for line in order.lines.all():
            PaymentEventQuantity.objects.create(
                event=event,
                line=line,
                quantity=line.quantity)

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

    def get_submitted_basket(self):
        basket_id = self.checkout_session.get_submitted_basket_id()
        return Basket._default_manager.get(pk=basket_id)

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
                self.request.basket = fzn_basket

    def send_confirmation_message(self, order, **kwargs):
        code = self.communication_type_code
        ctx = {'order': order,
               'lines': order.lines.all()}

        if not self.request.user.is_authenticated():
            path = reverse('customer:anon-order',
                           kwargs={'order_number': order.number,
                                   'hash': order.verification_hash()})
            site = Site.objects.get_current()
            ctx['status_url'] = 'http://%s%s' % (site.domain, path)

        try:
            event_type = CommunicationEventType.objects.get(code=code)
        except CommunicationEventType.DoesNotExist:
            # No event-type in database, attempt to find templates for this
            # type and render them immediately to get the messages
            messages = CommunicationEventType.objects.get_and_render(code, ctx)
            event_type = None
        else:
            # Create order event
            CommunicationEvent._default_manager.create(order=order,
                                                       event_type=event_type)
            messages = event_type.get_messages(ctx)

        if messages and messages['body']:
            logger.info("Order #%s - sending %s messages", order.number, code)
            dispatcher = Dispatcher(logger)
            dispatcher.dispatch_order_messages(order, messages,
                                               event_type, **kwargs)
        else:
            logger.warning("Order #%s - no %s communication event type",
                           order.number, code)
