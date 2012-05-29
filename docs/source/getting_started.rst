===============
Getting started
===============

Install using::

    pip install django-oscar

then add::

    'oscar.apps.basket.middleware.BasketMiddleware'

to ``MIDDLEWARE_CLASSES``, and::

    'oscar.apps.promotions.context_processors.promotions',
    'oscar.apps.checkout.context_processors.checkout',

to ``TEMPLATE_CONTEXT_PROCESSORS``.  Next, add the following apps
to your ``INSTALLED_APPS``::

    'oscar',
    'oscar.apps.analytics',
    'oscar.apps.discount',
    'oscar.apps.order',
    'oscar.apps.checkout',
    'oscar.apps.shipping',
    'oscar.apps.order_management',
    'oscar.apps.catalogue',
    'oscar.apps.catalogue.reviews',
    'oscar.apps.basket',
    'oscar.apps.payment',
    'oscar.apps.offer',
    'oscar.apps.address',
    'oscar.apps.partner',
    'oscar.apps.customer',
    'oscar.apps.promotions',
    'oscar.apps.reports',
    'oscar.apps.search',
    'oscar.apps.voucher',

Add::

    from oscar.defaults import *

to your ``settings`` module and run::

    python manage.py syncdb

to create the database tables.


Demo shop
---------

A demo shop is in preparation at the moment and will be available soon.

Real shop
---------

Sadly, setting up an e-commerce store is never trivial as you would like.  At a
minimum, you'll have to consider the following questions:

* How are shipping charges calculated?
* How are products organised into categories?
* How are stock messages determined?
* How is payment taken at checkout?
* How are orders fulfilled and managed?
* How is stock and inventory updated?

Much of the documentation for oscar is organised as recipes that explain
how to solve questions such as those above:

* :doc:`recipes/how_to_customise_an_app`
* :doc:`recipes/how_to_customise_models`
* :doc:`recipes/how_to_override_a_core_class`

