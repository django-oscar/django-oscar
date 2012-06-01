.. sphinx-quickstart on Mon Feb  7 13:16:33 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: http://img94.imageshack.us/img94/9094/oscarza.jpg

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
  subscriptions, variant products (eg a T-shirt in different sizes and colours).

* Customisable products, such as T-shirts with personalised messages.

* Can be used for large catalogues - Oscar is used in production by sites with
  more than 20 million products.

* Multiple fulfillment partners for the same product.

* Range of merchandising blocks for promoting products throughuout your site.

* Sophisticated offers that support virtually any kind of offer you can think
  of - multibuys, bundles, buy X get 50% of Y etc

* Vouchers

* Comprehensive dashboard

* Support for split payment orders

* Extension libraries available for PayPal, GoCardless, DataCash and more

Oscar is developed by `Tangent Labs`_, a London-based digital agency.  It is
used in production in several applications to sell everything from beer mats to
ipads.  The `source is on Github`_. 

.. _`Tangent Labs`: http://www.tangentlabs.co.uk
.. _`source is on Github`: https://github.com/tangentlabs/django-oscar

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

