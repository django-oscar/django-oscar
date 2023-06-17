.. spelling::

    DataCash

========================
How to integrate payment
========================

Oscar is designed to be very flexible around payment.  It supports paying for an
order with multiple payment sources and settling these sources at different
times.

Models
------

The payment app provides several models to track payments:

* ``SourceType`` - This is the type of payment source used (e.g. PayPal, DataCash).  As part of setting up
  a new Oscar site you would create a SourceType for each of the payment
  gateways you are using.
* ``Source`` - A source of payment for a single order.  This tracks how an order
  was paid for.  The source object distinguishes between allocations, debits and
  refunds to allow for two-phase payment model.  When an order is paid for by
  multiple methods, you create multiple sources for the order.
* ``Transaction`` - A transaction against a source.  These models provide better
  audit for all the individual transactions associated with an order.

Example
-------

Consider a simple situation where all orders are paid for by PayPal using their
'SALE' mode where the money is settled immediately (one-phase payment model).
The project would have a 'PayPal' SourceType and, for each order, create a new
``Source`` instance where the ``amount_debited`` would be the order total.  A
``Transaction`` model with ``txn_type=Transaction.DEBIT`` would normally also be
created (although this is optional).

This situation is implemented within the sandbox site for the
django-oscar-paypal_ extension.  Please use that as a reference.

See also the sandbox for django-oscar-datacash_ which follows a similar pattern.


.. _django-oscar-paypal: https://github.com/django-oscar/django-oscar-paypal/tree/master/sandbox
.. _django-oscar-datacash: https://github.com/django-oscar/django-oscar-datacash/tree/master/sandbox

Integration into checkout
-------------------------

By default, Oscar's checkout does not provide any payment integration as it is
domain-specific.  However, the core checkout classes  provide methods for
communicating with payment gateways and creating the appropriate payment models.

Payment logic is normally implemented by using a customised version of
``PaymentDetailsView``, where the ``handle_payment`` method is overridden.  This
method will be given the order number and order total plus any custom keyword
arguments initially passed to ``submit`` (as ``payment_kwargs``).  If payment is
successful, then nothing needs to be returned.  However, Oscar defines a few
common exceptions which can occur:

* ``oscar.apps.payment.exceptions.RedirectRequired``  For payment integrations
  that require redirecting the user to a 3rd-party site.  This exception class
  has a ``url`` attribute that needs to be set.

* ``oscar.apps.payment.exceptions.UnableToTakePayment`` For *anticipated* payment
  problems such as invalid bankcard number, not enough funds in account - that kind
  of thing.

* ``oscar.apps.payment.exceptions.UserCancelled`` During many payment flows,
  the user is able to cancel the process. This should often be treated
  differently from a payment error, e.g. it might not be appropriate to offer
  to retry the payment.

* ``oscar.apps.payment.exceptions.PaymentError``  For *unanticipated* payment
  errors such as the payment gateway not responding or being badly configured.

When payment has completed, there's a few things to do:

* Create the appropriate ``oscar.apps.payment.models.Source`` instance and pass
  it to ``add_payment_source``.  The instance is passed unsaved as it requires a
  valid order instance to foreign key to.  Once the order is placed (and an
  order instance is created), the payment source instances will be saved.

* Record a 'payment event' so your application can track which lines have been
  paid for.  The ``add_payment_event`` method assumes all lines are paid for by
  the passed event type, as this is the normal situation when placing an order.
  Note that payment events don't distinguish between different sources.

For example::

    from oscar.apps.checkout import views
    from oscar.apps.payment import models


    # Subclass the core Oscar view so we can customise
    class PaymentDetailsView(views.PaymentDetailsView):

        def handle_payment(self, order_number, total, **kwargs):
            # Talk to payment gateway.  If unsuccessful/error, raise a
            # PaymentError exception which we allow to percolate up to be caught
            # and handled by the core PaymentDetailsView.
            reference = gateway.pre_auth(order_number, total.incl_tax, kwargs['bankcard'])

            # Payment successful! Record payment source
            source_type, __ = models.SourceType.objects.get_or_create(
                name="SomeGateway")
            source = models.Source(
                source_type=source_type,
                amount_allocated=total.incl_tax,
                reference=reference)
            self.add_payment_source(source)

            # Record payment event
            self.add_payment_event('pre-auth', total.incl_tax)

Integrate ```cash on delivery```
================================

With cash-on-delivery, there is no need to handle payment in PaymentDetailsView. So you can just redirect from PaymentMethodView to preview, when 'cash-on-delivery' is selected:


Add PaymentSourceType "Cash on delivery":

.. code-block:: bash

    $ ./manage.py shell

.. code-block:: python

    from oscar.core.loading import get_model
    SourceType = get_model('payment', 'SourceType')
    SourceType.objects.create(name='Cash on delivery')

Subclass ```PaymentMethodView``` to redirect to preview

.. code-block:: python

    from django.shortcuts import redirect
    from django.urls import reverse
    from oscar.apps.checkout import views

    class PaymentMethodView(views.PaymentMethodView):

        def form_valid(self, form):
            """
            redirect to preview if payment_method == cash-on-delivery
            """
            payment_method = form.cleaned_data["payment_method"]
            self.checkout_session.pay_by(payment_method.code)
            if payment_method.code == 'cash-on-delivery':
                return redirect(reverse("checkout:preview"))
            return super().form_valid(form)
