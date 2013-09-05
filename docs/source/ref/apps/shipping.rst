========
Shipping
========

Shipping can be very complicated.  Depending on the domain, a wide variety of shipping
scenarios are found in the wild.  For instance, calculation of shipping costs can depend on:

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
-----------------

Shipping is handled using "method" objects which represent a means of shipping
an order (e.g., "standard" or "next-day" delivery).  Each method is essentially a
named calculator that takes a basket and is able to calculate the shipping
costs with and without tax.  

For example, you may model "standard" delivery by having a calculator object
that charges a fixed price for each item in the basket.  The method object
could be configured by passing the fixed price to be used for calculation.

Shipping within checkout
------------------------

Shipping is first encountered by customers within the checkout flow, on the "shipping
method" view.  

It is the responsibility of this class to either:

1. Offer an a set of delivery methods for the customer to choose from, displaying
   the cost of each.
2. If there is only one method available, to construct the appropriate shipping method
   and set it within the checkout session context.

The ``ShippingMethodView`` class handles this behaviour.  Its core
implementation looks up a list of available shipping methods using the
``oscar.shipping.repository.Repository`` class.  If there is only one, then
this is written out to the session and a redirect is issued to the next step of
the checkout.  If more than one, then each available method is displayed so the
customer can choose.

Default behaviour 
-----------------
Oscar ships with a simple model for calculating shipping based on a charge per
order, and a charge per item.  This is the ``OrderAndItemLevelChargeMethod``
class and is configured by setting the two charges used for the calculation.
You can use this model to provide multiple methods - each identified by a code.

The core ``Repository`` class will load all defined
``OrderAndItemLevelChargeMethod`` models and make them available to the
customer.  If none are set, then a `FreeShipping` method object will be
returned.  

Shipping method classes
-----------------------

Each method object must subclass ``ShippingMethod`` from
``oscar.shipping.methods`` which provides the required interface. Note that the interface
does not depend on the many other factors that can affect shipping (e.g., shipping address).  The
way to handle this is within your "factory" method which returns available shipping methods. 

Writing your own shipping method
--------------------------------

Simple really - follow these steps:  

1. Subclass ``oscar.shipping.methods.ShippingMethod`` and implement
   the methods ``basket_charge_incl_tax`` and ``basket_charge_excl_tax`` for calculating shipping costs.
2. Override the default ``shipping.repository.Repository`` class and implement your domain logic
   for determining which shipping methods are returned based on the user, basket and shipping address
   passed in.


Models
---------------

.. automodule:: oscar.apps.shipping.models
    :members:

Views
-----

None.

