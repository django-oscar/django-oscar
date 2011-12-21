.. django-oscar documentation master file, created by
   sphinx-quickstart on Mon Feb  7 13:16:33 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=============================================
Welcome to the documentation for django-oscar
=============================================

django-oscar is an ecommerce framework for Django, designed for building
domain-driven applications.  It is structured in way that lets any part of the
core functionality be customised to suit the needs of your project.  For
instance, if every product in your shop has an associated video, then
django-oscar lets you add such a field to your core product model.  You don't
have to model your domain logic using the Entity-Attribute-Value pattern or
other such meta-nastiness - your core models should reflect the specifics of
your domain.

django-oscar is developed by Tangent Labs, a London-based digital agency, and
is based on their existing Taoshop PHP platform which currently powers several
large-scale ecommerce sites.  

The source is on Github: https://github.com/tangentlabs/django-oscar.

Quick start
===========

We can do this quickly.  Create a virtualenv using virtualenvwrapper and
install django and django-oscar::

    mkvirtualenv --no-site-packages vanilla
    pip install django django-oscar

Take a copy of the sameple settings file, found at::

    https://github.com/tangentlabs/django-oscar/blob/master/examples/vanilla/settings_quickstart.py

Import the sample products and images::

    wget https://github.com/tangentlabs/django-oscar/blob/master/examples/sample-data/books-catalogue.csv
    python manage.py import_catalogue books-catalogue.csv

    wget https://github.com/tangentlabs/django-oscar/blob/master/examples/sample-data/book-images.tar.gz
    python manage.py import_images book-images.tar.gz

And there you have it: a fully functional ecommerce site with a product range of 100 popular books.

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
   design_decisions
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

