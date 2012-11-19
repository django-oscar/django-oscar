.. sphinx-quickstart on Mon Feb  7 13:16:33 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: http://img692.imageshack.us/img692/6498/logovf.png

===================================
Domain-driven e-commerce for Django
===================================

Oscar is an e-commerce framework for Django designed for building
domain-driven applications.  It is structured so that the core business objects
can be customised to suit the domain at hand.  In this way, your application
can accurately model its domain, making feature development and maintenance
much easier.

Features:

* Any product type can be handled, including downloadable products,
  subscriptions, variant products (e.g., a T-shirt in different sizes and colours).

* Customisable products, such as T-shirts with personalised messages.

* Can be used for large catalogues - Oscar is used in production by sites with
  more than 20 million products.

* Multiple fulfillment partners for the same product.

* Range of merchandising blocks for promoting products throughout your site.

* Sophisticated offers that support virtually any kind of offer you can think
  of - multi-buys, bundles, buy X get 50% off Y etc

* Vouchers

* Comprehensive dashboard

* Support for split payment orders

* Extension libraries available for PayPal, GoCardless, DataCash and more

Oscar is a good choice if your domain has non-trivial business logic.  Oscar's
flexibility means it's straightforward to implement business rules that would be
difficult to apply in other frameworks.  

Example requirements that Oscar applications already handle:

* Paying for an order with multiple payment sources (e.g., using a bankcard,
  voucher, gift card and business account).

* Complex access control rules governing who can view and order what.

* Supporting a hierarchy of customers, sales reps and sales directors - each
  being able to "masquerade" as their subordinate users.

* Multi-lingual products and categories

Oscar is developed by `Tangent Labs`_, a London-based digital agency.  It is
used in production in several applications to sell everything from beer mats to
ipads.  The `source is on GitHub`_ - contributions welcome.

.. _`Tangent Labs`: http://www.tangentlabs.co.uk
.. _`source is on GitHub`: https://github.com/tangentlabs/django-oscar

.. toctree::
   :maxdepth: 2

   take_a_peek
   getting_started
   key_questions
   recipes
   getting_help
   design_decisions
   reference
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

