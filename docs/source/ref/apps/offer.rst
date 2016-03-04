======
Offers
======

Oscar ships with a powerful and flexible offers engine which is contained in the
offers app.  It is based around the concept of 'conditional offers' - that is,
a basket must satisfy some condition in order to qualify for a benefit.

Oscar's dashboard can be used to administer offers.

Structure
---------

A conditional offer is composed of several components:

* Customer-facing information - this is the name and description of an offer.
  These will be visible on offer-browsing pages as well as within the basket and
  checkout pages.

* Availability - this determines when an offer is available.

* Condition - this determines when a customer qualifies for the offer (eg spend
  £20 on DVDs).  There are various condition types available.

* Benefit - this determines the discount a customer receives.  The discount can
  be against the basket cost or the shipping for an order.

Availability
------------

An offer's availability can be controlled by several settings which can be used
in isolation or combination:

* Date range - a date can be set, outside of which the offer is unavailable.

* Max global applications - the number of times an offer can be used can be capped.
  Note that an offer can be used multiple times within the same order so this
  isn't the same as limiting the number of orders that can use an offer.

* Max user applications - the number of times a particular user can use an
  offer.  This makes most sense to use in sites that don't allow anonymous
  checkout as it could be circumvented by submitting multiple anonymous orders.

* Max basket applications - the number of times an offer can be used for a
  single basket/order.

* Max discount - the maximum amount of discount an offer can give across all
  orders.  For instance, you might have a marketing budget of £10000 and so you
  could set the max discount to this value to ensure that once £10000 worth of
  benefit had been awarded, the offer would no longer be available.  Note that
  the total discount would exceed £10000 as it would have to cross this
  threshold to disable the offer.

Conditions
----------

There are 3 built-in condition types that can be created via the dashboard.
Each needs to be linked with a range object, which is subset of the product
catalogue.  Ranges are created independently in the dashboard.

* Count-based - ie a customer must buy X products from the condition range
* Coverge-based - ie a customer must buy X DISTINCT products from the condition range.  This can be used to
  create "bundle" offers.
* Value-based - ie a customer must spend X on products from the condition range

It is also possible to create custom conditions in Python and register these so they
are available to be selected within the dashboard.  For instance, you could
create a condition that specifies that the user must have been registered for
over a year to qualify for the offer.

Under the hood, conditions are defined by 3 attributes: a range, a type
and a value.

Benefits
--------

There are several types of built-in benefit, which fall into one of two
categories: benefits that give a basket discount, and those that give a shipping
discount.

Basket benefits:

* Fixed discount - ie get £5 off DVDs
* Percentage discount - ie get 25% off books
* Fixed price - ie get any DVD for £8
* Multibuy - ie get the cheapest product that meets the condition for free

Shipping benefits (these largely mirror the basket benefits):

* Fixed discount - ie £5 off shipping
* Percentage discount - ie get 25% off shipping
* Fixed price - ie get shipping for £8

Like conditions, it is possible to create a custom benefit.  An example might be
to allow customers to earn extra credits/points when they qualify for some
offer.  For example, spend £100 on perfume, get 500 credits (note credits don't
exist in core Oscar but can be implemented using the 'accounts' plugin).

Under the hood, benefits are modelled by 4 attributes: a range, a type, a value
and a setting for the maximum number of basket items that can be affected by a
benefit.  This last settings is useful for limiting the scope of an offer.  For
instance, you can create a benefit that gives 40% off ONE products from a given
range by setting the max affected items to 1.  Without this setting, the benefit
would give 40% off ALL products from the range.

Benefits are slightly tricky in that some types don't require a range and ignore
the value of the max items setting.

Examples
--------

Here's some example offers:

*3 for 2 on books*
    1. Create a range for all books.
    2. Use a **count-based** condition that links to this range with a value of 3.
    3. Use a **multibuy** benefit with no value (the value is implicitly 1)

*Spend £20 on DVDs, get 25% off*
    1. Create a range for all DVDs.
    2. Use a **value-based** condition that links to this range with a value of 20.
    3. Use a **percentage discount** benefit that links to this range and has a
       value of 25.

*Buy 2 Lonely Planet books, get £5 off a Lonely Planet DVD*
    1. Create a range for Lonely Planet books and another for Lonely Planet DVDs
    2. Use a **count-based** condition linking to the book range with a value of 2
    3. Use a **fixed discount** benefit that links to the DVD range and has a value of 5.

More to come...

Abstract models
---------------

.. automodule:: oscar.apps.offer.abstract_models
    :members:

Models
-------

.. automodule:: oscar.apps.offer.models
    :members:

Views
-----

.. automodule:: oscar.apps.offer.views
    :members:
