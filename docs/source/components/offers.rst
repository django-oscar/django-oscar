===================
Offers and vouchers
===================

The ``oscar.offers`` app offers functionality for basket-level offers and vouchers.  This covers
features such as:

* 3 for 2 offers on fiction books
* Buy one book, get a DVD for half price
* A Christmas voucher code that gives 25% off all products until Decmember 25th
* All students get £5 off their first order
* Visitors coming from an affiliate site get 10% off their order

In short, it is very flexible.

Conditional offers
------------------
A conditional offer is defined by two things:

* A *Condition*, which is some criteria that the user's basket has to have met.  These are
  either count- (eg must contain one fiction book) or value-based (eg must contain £10 or more
  of DVDs).
* A *Benefit*, which is the discount that is applied to the basket.

When an offer is applied the basket, the products that are used to meet the condition, and the
products discounted by the benefit are "consumed" so that they are not available for other offers.

Vouchers
--------
A voucher is essentially a code which links through to a set of offers.
