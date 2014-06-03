.. image:: ../images/logos/oscar.png
   :align: right

=====
Oscar
=====

-----------------------------------
Domain-driven e-commerce for Django
-----------------------------------

Oscar is an e-commerce framework for building domain-driven applications. It
has flexibility baked into its core so that complicated requirements can be
elegantly captured. You can tame a spaghetti domain without writing spaghetti
code.

Oscar is maintained by `Tangent Snowball`_, who are experts in building complex
transactional sites for both B2C and B2B markets. Years of e-commerce
hard-earned experience informs Oscar's design. 

.. _`Tangent Snowball`: http://www.tangentsnowball.com/

Oscar is "domain-driven" in the sense that the core business objects can be
customised to suit the domain at hand. In this way, your application can
accurately capture the subtleties of its domain, making feature development and
maintenance much easier.

Features:

* Any product type can be handled including downloadable products,
  subscriptions, variant products (e.g., a T-shirt in different sizes and colours).

* Customisable products, such as T-shirts with personalised messages.

* Large catalogue support - Oscar is used in production by sites with
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

Example requirements that Oscar projects already handle:

* Paying for an order with multiple payment sources (e.g., using a bankcard,
  voucher, gift card and points account).

* Complex access control rules governing who can view and order what.

* Supporting a hierarchy of customers, sales reps and sales directors - each
  being able to "masquerade" as their subordinates.

* Multi-lingual products and categories.

* Digital products.

* Dynamically priced products (eg where the price is provided by an external
  service).

Oscar is used in production in several applications to sell everything from beer
mats to iPads.  The `source is on GitHub`_ - contributions are always welcome.

.. _`Tangent Labs`: http://www.tangentlabs.co.uk
.. _`source is on GitHub`: https://github.com/tangentlabs/django-oscar

.. toctree::
   :hidden:
   :maxdepth: 2

   internals/getting_started
   topics/key_questions
   topics/customisation
   ref/index
   internals/contributing/index
   releases/index

First steps
===========

- :doc:`internals/sandbox`
- :doc:`internals/getting_started`
- :doc:`topics/key_questions`
- :doc:`internals/getting_help`
- :doc:`ref/glossary`

Using Oscar
===========

All you need to start developing an Oscar project.

- :doc:`topics/customisation`
- :doc:`topics/class_loading_explained`
- :doc:`topics/prices_and_availability`
- :doc:`topics/deploying`
- :doc:`topics/translation`
- :doc:`topics/upgrading`

Reference:

- :doc:`Core functionality </ref/core>`
- :doc:`Oscar's apps </ref/apps/index>`
- :doc:`howto/index`
- :doc:`ref/settings`
- :doc:`ref/signals`

The Oscar open-source project
=============================

Learn about the ideas behind Oscar and how you can contribute.

- :doc:`internals/design-decisions`
- :doc:`releases/index`
- :doc:`internals/contributing/index`
