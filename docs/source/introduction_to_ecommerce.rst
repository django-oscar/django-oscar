================
eCommerce domain
================

When building an e-commerce site, there are several components whose
implementation is strongly domain-specific.  That is, every site will have
different requirements for how such a component should operate.  As such, these components
cannot easily be modelled using a generic system - no configurable system will be able
to accurately capture all the domain-specific behaviour required.  

The design philosophy of oscar is to not make a decision for you here, but to
provide the environment where any domain logic can be implemented, no matter
how complex.  This is achieved through the use of subclassable objects that can 
be tailored to your domain. 

This document lists the components which will require implementation according to the
domain:

Taxonomy
--------
How are products organised within the site?  A common pattern is to have a single 
"category tree" where each product belongs to one category which sits within a tree structure
of other categories?

However, there are lots of other options such as having several separate taxonomy trees (eg split by
brand, by theme, by product type).

* Can a product belong to more than one category?
* Can a category sit in more than one place within the tree?  (eg a "children's fiction" category
  might sit beneath "children's books" and "fiction").

Payment flow
------------
* Will the customer be debited at point of checkout, or when the items are dispatched?
* If charging after checkout, when are shipping charges collected?  
* What happens if an order is cancelled after partial payment?

Payment sources
---------------
How are customers going to pay for orders?  

Will it be a simple, single-payment source solution such as paying by bankcard or using 
Google checkout?  Or something more complicated such as allowing payment to be split across
multiple payment sources such as a bankcard and a giftcard?

More commonly, multiple payment sources can be used - such as:

* Bankcard
* Google checkout
* PayPal
* Business account
* Managed budget
* No upfront payment but send invoices later
* Giftcard

The checkout app within django-oscar is suitable flexible that all of these methods (and in 
any combination) is supported.  However, you will need to implement the logic for your domain
by subclassing the relevant view/util classes. 

Domain logic is often required to: 

* Determine which sources are available to an order;
* Determine if payment can be split across sources and in which combinations;
* Determine the order in which to take payment

Stock logic
-----------
* Does the site support pre-orders (ordering before the product is available to be shipped) or
  back-orders (ordering when the product does not have stock)?  

Availability
------------
* Based on the stock information from a fulfilment partner, what messaging should be 
  displayed on the site?  Further, should

Shipping
--------
Every client has a different requirement for shipping charges.  At its core, shipping charges
normall depend on the following:

* Items in basket
* Shipping method chosen (e.g., standard or courier delivery)
* Dispatch method chosen (e.g., ship together or ship separately)
* Shipping address (e.g., which country it is in)
* Basket vouchers (e.g., a voucher which gives free delivery)

Common questions:

* Are items shipping together as one batch, or separately?

Checkout
--------



