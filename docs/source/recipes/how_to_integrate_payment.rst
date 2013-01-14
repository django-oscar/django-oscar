========================
How to integrate payment
========================

Oscar is designed to be very flexible around payment.  It supports paying for an
order with multiple payment sources and settling these sources at different
times.

Models
------

The payment app provides several models to track payments:

* ``SourceType`` - This is the type of payment source used (eg PayPal, DataCash, BrainTree).  As part of setting up
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
``Source`` instance where the ``amount_debitted`` would be the order total.  A
``Transaction`` model with ``txn_type=Transaction.DEBIT`` would normally also be
created (although this is optional).

This situation is implemented within the sandbox site for the
django-oscar-paypal_ extension.  Please use that as a reference.  

.. _django-oscar-paypal: https://github.com/tangentlabs/django-oscar-paypal/tree/develop/sandbox

See also the sandbox for django-oscar-datacash which follows a similar pattern.

Integration into checkout
-------------------------

By default, Oscar's checkout does not provide any payment integration as it is
domain-specific.  However, the core checkout classes do provide methods for
creating payment sources.

Payment logic is normally implemented by overriding the ``handle_payment``
method.  When payment has completed, there's a few things to do:

* Create the appropriate Source instance and pass it to ``add_payment_source``.
  The instance is passed unsaved as it can't be saved until there is a valid
  order instance to foreign key to.

* Record a 'payment event' so your application can track which lines have been
  paid for.  The ``add_payment_event`` method assumes all lines are paid for by
  the passed event type, as this is the normal situation when placing an order.
  Note that payment events don't distinguish between different sources.
  
For example::

    from oscar.apps.payment import models

    def handle_payment(self, order_number, total_incl_tax, **kwargs):
        # Talk to payment gateway.  If unsuccessful/error, raise an exception
        reference = gateway.pre_auth(order_number, total_incl_tax, kwargs['bankcard'])

        # Record payment source
        source_type, __ = models.SourceType.objects.get_or_create(
            name="SomeGateway")
        source = models.Source(
            source_type=source_type,
            amount_allocated=total_incl_tax,
            reference=reference)
        self.add_payment_source(source)

        # Record payment event
        self.add_payment_event('pre-auth', total_incl_tax)
