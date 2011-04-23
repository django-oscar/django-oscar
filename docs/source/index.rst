.. django-oscar documentation master file, created by
   sphinx-quickstart on Mon Feb  7 13:16:33 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=============================================
Welcome to the documentation for django-oscar
=============================================

django-oscar is a flexible e-commerce platform for Django, designed to build domain-driven
ecommerce sites.  It differs from other e-commerce projects in that the core of django-oscar is kept
quite small but extensible.  Any class within oscar can be subclassed and extended to customise
the functionality available.  While this means that more work is required up-front to 
set up the model, form and utility classes, the resulting project should be
a much better representation of the domain at hand.

It is developed by Tangent Labs, a London-based digital agency, and is based on
their existing Taoshop PHP platform which currently powers several large-scale ecommerce sites.  

It is still in early development, but a stable release is planned for early summer 2011.
The source is on Github: https://github.com/tangentlabs/django-oscar

Getting started:

.. toctree::
    :maxdepth: 2
    :numbered:

    contributing
    getting_started


Full contents:

.. toctree::
   :maxdepth: 2

   introduction
   ecommerce_domain
   getting_started
   components
   web_services
   recipes
   contributing
   reference

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

