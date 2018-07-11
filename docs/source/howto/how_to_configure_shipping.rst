=========================
How to configure shipping
=========================

Shipping can be very complicated.  Depending on the domain, a wide variety of
shipping scenarios are found in the wild.  For instance, calculation of
shipping costs can depend on:

* Shipping method (e.g., standard, courier)
* Shipping address
* Time of day of order (e.g., if requesting next-day delivery)
* Weight of items in basket
* Customer type (e.g., business accounts get discounted shipping rates)
* Offers and vouchers that give free or discounted shipping

Further complications can arise such as:

* Only making certain shipping methods available to certain customers
* Tax is only applicable in certain situations

Oscar can handle all of these shipping scenarios.

Shipping in Oscar
~~~~~~~~~~~~~~~~~

Configuring shipping charges requires overriding Oscar's core 'shipping' app
and providing your own ``Repository`` class (see :doc:`/topics/customisation`) that
returns your chosen shipping method instances.

The primary responsibility of the
``Repository`` class is to provide the available shipping methods for a
particular scenario. This is done via the
:func:`~oscar.apps.shipping.repository.Repository.get_shipping_methods` method,
which returns the shipping methods available to the customer.

This method is called in several places:

* To look up a "default" shipping method so that sample shipping charges can be
  shown on the basket detail page.

* To list the available shipping methods on the checkout shipping method page.

* To check the selected shipping method is still available when an order is
  submitted.

The ``get_shipping_methods`` method takes the basket, user, shipping address
and request as parameters. These can be used to provide different sets of
shipping methods depending on the circumstances. For instance, you could use
the shipping address to provide international shipping rates if the address is
overseas.

The ``get_default_shipping_method`` method takes the same parameters and
returns default shipping method for the current basket. Used for shipping
cost indication on the basket page. Defaults to free shipping method.

.. note::

    Oscar's checkout process includes a page for choosing your shipping method.
    If there is only one method available for your basket (as is the default)
    then it will be chosen automatically and the user immediately redirected to
    the next step.

Custom repositories
-------------------

If the available shipping methods are the same for all customers and shipping
addresses, then override the ``methods`` property of the repository:

.. code-block:: python

   from oscar.apps.shipping import repository
   from . import methods

   class Repository(repository.Repository):
       methods = (methods.Standard(), methods.Express())

For more complex logic, override the ``get_available_shipping_methods`` method:

.. code-block:: python

   from oscar.apps.shipping import repository
   from . import methods

   class Repository(repository.Repository):

       def get_available_shipping_methods(self, basket, user=None, shipping_addr=None, request=None, **kwargs):
           methods = (methods.Standard(),)
           if shipping_addr and shipping_addr.country.code == 'GB':
               # Express is only available in the UK
               methods = (methods.Standard(), methods.Express())
           return methods

Note that the ``get_shipping_methods`` method wraps
``get_available_shipping_methods`` in order to handle baskets that don't
require shipping and to apply shipping discounts.

Shipping methods
----------------

Shipping methods need to implement a certain API. They need to have the
following properties which define the metadata about the shipping method:

* ``code`` - This is used as an identifier for the shipping method and so should
  be unique amongst the shipping methods available in your shop.

* ``name`` - The name of the shipping method. This will be visible to the
  customer during checkout.

* ``description`` - An optional description of the shipping method. This can
  contain HTML.

Further, each method must implement a ``calculate`` method which accepts the
basket instance as a parameter and returns a ``Price`` instance.  Most shipping
methods subclass
:class:`~oscar.apps.shipping.methods.Base`, which stubs this API.

Here's an example:

.. code-block:: python

   from oscar.apps.shipping import methods
   from oscar.core import prices

   class Standard(methods.Base):
       code = 'standard'
       name = 'Standard shipping (free)'

       def calculate(self, basket):
           return prices.Price(
               currency=basket.currency,
               excl_tax=D('0.00'), incl_tax=D('0.00'))

Core shipping methods
~~~~~~~~~~~~~~~~~~~~~

Oscar ships with several re-usable shipping methods which can be used as-is, or
subclassed and customised:

* :class:`~oscar.apps.shipping.methods.Free` - no shipping charges

* :class:`~oscar.apps.shipping.methods.FixedPrice` - fixed-price shipping charges.
  Example usage:

.. code-block:: python

   from oscar.apps.shipping import methods
   from oscar.core import prices

   class Standard(methods.FixedPrice):
       code = 'standard'
       name = 'Standard shipping'
       charge_excl_tax = D('5.00')

   class Express(methods.FixedPrice):
       code = 'express'
       name = 'Express shipping'
       charge_excl_tax = D('10.00')

There is also a weight-based shipping method,
:class:`~oscar.apps.shipping.abstract_models.AbstractWeightBased`
which determines a shipping charge by calculating the weight of a basket's
contents and looking this up in a model-based set of weight bands.

