===================
Offers and vouchers
===================

The ``oscar.offers`` app offers functionality for basket-level offers and vouchers.  This covers
features such as:

* 3-for-2 offers on fiction books
* Buy one book, get a DVD for half price
* A Christmas voucher code that gives 25% off all products until December 25th
* All students get £5 off their first order
* Visitors coming from an affiliate site get 10% off their order
* A voucher code that can be used once by each customer and gives 25% off

In short, it is very flexible.

Basket-level offers
-------------------
A conditional offer has metadata such as a name, description and date range (for when it is active) 
but is defined by two things:

* A *Condition*, which is some criteria that the user's basket has to have met.  These are
  either count- (e.g., must contain one fiction book) or value-based (e.g., must contain £10 or more
  of DVDs).
* A *Benefit*, which is the discount that is applied to the basket.

When an offer is applied the basket, the products that are used to meet the condition, and the
products discounted by the benefit are "consumed" so that they are not available for other offers.

Offers come in 4 types:

* *Site offers* - Offers that are available to all users of the site.  Every time a basket is looked
  up for a user, we attempt to apply these offers to give a discount.  An example is a "3 for 2" offer 
  on all fiction books.

* *Voucher offers* - Offers that are available if you have attached a specific voucher code to your basket.
  For example, a voucher could be created that links to a 25% off offer on all products.

* *User offers* - Offers available only to certain users - these are looked up by passing the ``auth.User`` 
  object to a look-up service that returns any relevant offers.  This could be used to give student 
  users a discount or something like that.

* *Session offers* - Offers available for the duration of the current session.  These have to be inserted
  into the session by some mechanism, but exist to allow functionality such as giving discount to 
  users that come from an affiliate site.

In practice, all these offers are loaded and merged into a single set which is then applied to the basket.

When creating an offer, you need to specify which type of offer it is.

Vouchers
--------

A voucher is essentially a code which links through to a set of basket-level
offers (see above).  Note that you can have any number of vouchers attached to
a basket.


Basket discounts
----------------

* *Multibuy* - This gives the cheapest product in the condition range for free.
  This is normally used to build 3-for-2 offers and similar.

* *Percentage discount* - A percentage discount off the basket products that are
  in the benefit range.

* *Absolute discount* - An absolute discount off the basket products in the
  benefit range.

* *Fixed price* - 

* 


