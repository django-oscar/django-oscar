.. image:: ../images/logos/oscar.png
   :align: right

=====
Oscar
=====

-----------------------------------
Domain driven e-commerce for Django
-----------------------------------


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

* A range of merchandising blocks for promoting products throughout your site.

* Sophisticated offers that support virtually any kind of offer you can think
  of - multi-buys, bundles, buy X get 50% off Y etc

* Vouchers (built on top of the offers framework)

* Comprehensive dashboard that replaces the Django admin completely

* Support for complex order processing such split payment orders, multi-batch
  shipping, order status pipelines.

* Extension libraries available for many payment gateways, including PayPal_,
  GoCardless_, DataCash_ and more.

.. _PayPal: https://github.com/tangentlabs/django-oscar-paypal
.. _GoCardless: https://github.com/tangentlabs/django-oscar-gocardless
.. _DataCash: https://github.com/tangentlabs/django-oscar-datacash

Oscar is a good choice if your domain has non-trivial business logic.  Oscar's
flexibility means it's straightforward to implement business rules that would be
difficult to apply in other frameworks.  

Example requirements that Oscar applications already handle:

* Paying for an order with multiple payment sources (e.g., using a bankcard,
  voucher, gift card and business account).

* Complex access control rules governing who can view and order what.

* Supporting a hierarchy of customers, sales reps and sales directors - each
  being able to "masquerade" as their subordinates.

* Multi-lingual products and categories.

* Digital products.

* Dynamically priced products (eg where the price is provided by an external
  service).

Oscar is developed by `Tangent Labs`_, a London-based digital agency.  It is
used in production in several applications to sell everything from beer mats to
ipads.  The `source is on GitHub`_ - contributions welcome.

.. _`Tangent Labs`: http://www.tangentlabs.co.uk
.. _`source is on GitHub`: https://github.com/tangentlabs/django-oscar

First steps
===========
.. toctree::
   :maxdepth: 1

   internals/sandbox
   internals/getting_started
   topics/key_questions
   internals/getting_help
   ref/glossary

Using Oscar
===========

All you need to start developing an Oscar project.

.. toctree::
   :maxdepth: 1

   topics/customisation
   topics/prices_and_availability
   topics/deploying
   topics/translation
   topics/upgrading

Reference:

.. toctree::
   :maxdepth: 1

   Core functionality </ref/core>
   Oscar's apps </ref/apps/index>
   howto/index
   ref/settings
   ref/signals

The Oscar open-source project
=============================

Learn about the ideas behind Oscar and how you can contribute.

.. toctree::
   :maxdepth: 1

   internals/design-decisions
   releases/index
   internals/contributing/index
   
