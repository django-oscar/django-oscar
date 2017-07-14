import logging
import six

from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib import messages
from django.contrib.sites.models import Site, get_current_site
from django.utils.translation import ugettext as _

from oscar.core.loading import get_class, get_classes, get_model

from . import signals

Basket = get_model('basket', 'Basket')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')
Clerk = get_class('checkout.clerk', 'Clerk')

PaymentRedirectRequired, UnableToTakePayment, PaymentError \
    = get_classes('payment.exceptions', ['RedirectRequired',
                                         'UnableToTakePayment',
                                         'PaymentError'])

# Standard logger for checkout events
logger = logging.getLogger('oscar.checkout')


class RedirectRequired(Exception):
    def __init__(self, target):
        self.target = target


class CheckoutFailed(Exception):
    pass


class OrderPlacementMixin(CheckoutSessionMixin):
    # Payment handling methods
    # ------------------------

    def handle_payment(self, basket_id, order_number, total, **kwargs):
        """
        Handle any payment processing and record payment sources and events.

        This method is designed to be overridden within your project.  The
        default is to do nothing as payment is domain-specific.

        This method is responsible for handling payment and recording the
        payment sources (using the add_payment_source method) and payment
        events (using add_payment_event) so they can be
        linked to the order when it is saved later on.
        """
        return [], []

    def do_payment(self, clerk):
        # We define a general error message for when an unanticipated payment
        # error occurs.
        error_msg = _("A problem occurred while processing payment for this "
                      "order - no payment has been taken.  Please "
                      "contact customer services if this problem persists")

        signals.pre_payment.send_robust(sender=self, view=self)

        try:
            payment_sources, payment_events = (
                self.handle_payment(clerk.basket.pk, clerk.order_number,
                                    clerk.order_total))
        except PaymentRedirectRequired as e:
            # Redirect required (eg PayPal, 3DS)
            logger.info("Order #%s: redirecting to %s", clerk.order_number,
                        e.url)
            raise RedirectRequired(e.url)
        except UnableToTakePayment as e:
            # Something went wrong with payment but in an anticipated way.  Eg
            # their bankcard has expired, wrong card number - that kind of
            # thing. This type of exception is supposed to set a friendly error
            # message that makes sense to the customer.
            msg = six.text_type(e)
            logger.warning(
                "Order #%s: unable to take payment (%s) - restoring basket",
                clerk.order_number, msg)
            self.restore_frozen_basket()

            # We assume that the details submitted on the payment details view
            # were invalid (eg expired bankcard).
            # TODO: make it so that payment details are next up
            messages.error(self.request, msg)
            raise CheckoutFailed
        except PaymentError as e:
            # A general payment error - Something went wrong which wasn't
            # anticipated.  Eg, the payment gateway is down (it happens), your
            # credentials are wrong - that king of thing.
            # It makes sense to configure the checkout logger to
            # mail admins on an error as this issue warrants some further
            # investigation.
            msg = six.text_type(e)
            logger.error("Order #%s: payment error (%s)", clerk.order_number,
                         msg, exc_info=True)
            self.restore_frozen_basket()
            messages.error(self.request, error_msg)
            raise CheckoutFailed
        except Exception as e:
            # Unhandled exception - hopefully, you will only ever see this in
            # development...
            logger.error(
                "Order #%s: unhandled exception while taking payment (%s)",
                clerk.order_number, e, exc_info=True)
            self.restore_frozen_basket()
            messages.error(self.request, error_msg)
            raise CheckoutFailed

        signals.post_payment.send_robust(sender=self, view=self)

        return payment_sources, payment_events

    # Order submission methods
    # ------------------------

    def get_clerk(self, **kwargs):
        submission = self.build_submission(**kwargs)

        clerk = Clerk(submission['user'], submission['basket'])
        clerk.shipping_method = submission['shipping_method']
        clerk.shipping_address = submission['shipping_address']
        clerk.billing_address = submission['billing_address']

        if 'status' in submission['order_kwargs']:
            clerk.order_status = submission['order_kwargs'].pop('status')

        if 'guest_email' in submission['order_kwargs']:
            clerk.guest_email = submission['order_kwargs'].pop('guest_email')

        return clerk

    # Post-order methods
    # ------------------

    def handle_successful_order(self, order):
        """
        Handle the various steps required after an order has been successfully
        placed.

        Override this view if you want to perform custom actions when an
        order is submitted.
        """
        # Save order id in session so thank-you page can load it
        self.request.session['checkout_order_id'] = order.id

    def send_confirmation_message(self, order, code, **kwargs):
        pass

    def get_message_context(self, order):
        ctx = {
            'user': self.request.user,
            'order': order,
            'site': get_current_site(self.request),
            'lines': order.lines.all()
        }

        if not self.request.user.is_authenticated():
            # Attempt to add the anon order status URL to the email template
            # ctx.
            try:
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
