=========================
How to configure shipping
=========================

Checkout flow
-------------

Oscar's checkout is set-up to follow the following steps:

1. Manage basket
2. Enter/choose shipping address
3. Choose shipping method
4. Choose payment method
5. Preview
6. Enter payment details and submit

Determining the methods available to a user
-------------------------------------------

At the shipping method stage, we use a repository object to look up the
shipping methods available to the user.  These methods typically depend on:

* the user in question (e.g., staff get cheaper shipping rates)
* the basket (e.g., shipping is charged based on the weight of the basket)
* the shipping address (e.g., overseas shipping is more expensive)

The default repository is ``oscar.apps.shipping.repository.Repository``, which 
has a method ``get_shipping_methods`` for returning all available methods.  By
default, the returned method will be ``oscar.apps.shipping.methods.Free``.

Set a custom shipping methods
-----------------------------

To apply your domain logic for shipping, you will need to override
the default repository class (see :doc:`how_to_override_a_core_class`) and alter
the implementation of the ``get_shipping_methods`` method.  This method
should return a list of "shipping method" classes already instantiated
and holding a reference to the basket instance.

Building a custom shipping method
---------------------------------

A shipping method class must define two methods::

    method.basket_charge_incl_tax()
    method.basket_charge_excl_tax()

whose responsibilities should be clear.  You can subclass ``oscar.apps.shipping.base.ShippingMethod``
to provide the basic functionality.

Built-in shipping methods
-------------------------

Oscar comes with several built-in shipping methods which are easy to use
with a custom repository.

* ``oscar.apps.shipping.methods.Free``.  No shipping charges.

* ``oscar.apps.shipping.methods.WeightBased``.  This is a model-driven method
  that uses two models: ``WeightBased`` and ``WeightBand`` to provide charges
  for different weight bands.  By default, the method will calculate the weight
  of a product by looking for a 'weight' attribute although this can be
  configured.  

* ``oscar.apps.shipping.methods.FixedPrice``.  This simply charges a fixed price for 
  shipping, irrespective of the basket contents.

* ``oscar.apps.shipping.methods.OrderAndItemCharges``.  This is a model which
  specifies a per-order and a per-item level charge.
