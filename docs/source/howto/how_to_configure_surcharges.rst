.. _how_to_surcharges:

=========================
How to configure surcharges
=========================

A surcharge, also known as checkout fee, is an extra fee charged by a merchant when receiving a payment by cheque, credit card, charge card or debit card (but not cash) which at least covers the cost to the merchant of accepting that means of payment, such as the merchant service fee imposed by a credit card company.


Surcharges in Oscar
~~~~~~~~~~~~~~~~~

Configuring surcharges requires overriding Oscar's core 'checkout' app
and providing your own ``SurchargeApplicator`` class (see :doc:`/topics/customisation`) that
returns your chosen surcharge instances.

The primary responsibility of the
``SurchargeApplicator`` class is to provide the available surcharge methods for a
particular scenario. This is done via the
:func:`~oscar.apps.checkout.applicator.SurchargeApplicator.get_applicable_surcharges` method,
which returns the surcharges available to the customer.

This method is called in several places:

* To look up the "default" surcharges so that sample surcharges can be
  shown on the basket detail page.

* To give the applicable surcharges to the order total calculator so wo can show the correct price breakdown.

The ``get_applicable_surcharges`` method takes the basket and any other kwargs.
These kwargs can later be determined when setting up your own surcharges.

Note that you can also implement surcharges as models just like shipping methods.

Custom applicators
-------------------

If the available surcharges are the same for all customers and payment
methods, then override the ``get_surcharges`` method of the repository:

.. code-block:: python

   from decimal import Decimal as D
   from oscar.apps.checkout import applicator
   from . import surcharges

   class SurchargeApplicator(applicator.SurchargeApplicator):
       def get_surcharges(self, basket, **kwargs):
           return (
               surcharges.PercentageCharge(percentage=D("2.00")),
           )

For more complex logic, override the ``is_applicable`` method:

.. code-block:: python

   from oscar.apps.checkout import applicator

   class SurchargeApplicator(applicator.SurchargeApplicator):

       def is_applicable(self, surcharge, basket, **kwargs):
           payment_method_code = kwargs.get("payment_method_code", None)
           if payment_method is not None and payment_method_code == "paypal":
               return True
           else:
               return False


Surcharges
----------------

Surcharges need to implement a certain API. They need to have the
following properties which define the metadata about the surcharge:

* ``name`` - The name of the surcharges. This will be visible to the
  customer during checkout and is translatable

* ``code`` - The code of the surcharge. This could be the slugified name or anything else.
  The code is used as a non-translatable identifier for a charge.

Further, each surcharge must implement a ``calculate`` method which accepts the
basket instance as a parameter and returns a ``Price`` instance.  Most surcharges
subclass
:class:`~oscar.apps.checkout.surcharges.BaseSurcharge`, which stubs this API.


Core surcharges
~~~~~~~~~~~~~~~~~~~~~

Oscar ships with several re-usable surcharges which can be used as-is, or
subclassed and customised:

* :class:`~oscar.apps.checkout.surcharges.PercentageCharge` - percentage based charge

* :class:`~oscar.apps.checkout.surcharges.FlatCharge` - flat surcharge

  Example usage:

.. code-block:: python

   from decimal import Decimal as D
   from oscar.apps.checkout import surcharges

   percentage_charge = surcharges.PercentageCharge(percentage=D("2.00"))
   flat_charge = surcharges.FlatCharge(excl_tax=D("10.00"), incl_tax=D("12.10"))
