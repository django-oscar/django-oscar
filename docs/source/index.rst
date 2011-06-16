.. django-oscar documentation master file, created by
   sphinx-quickstart on Mon Feb  7 13:16:33 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=============================================
Welcome to the documentation for django-oscar
=============================================

django-oscar is a ecommerce framework for Django 1.3 for building domain-driven
ecommerce sites.  It is structured in way that lets any part of the core
ecommerce functionality be customised to suit the needs of your project.    

It is developed by Tangent Labs, a London-based digital agency, and is based on
their existing Taoshop PHP platform which currently powers several large-scale ecommerce sites.  

It is still in early development, but a stable release is planned for early summer 2011.
The source is on Github: https://github.com/tangentlabs/django-oscar - all contributions welcome.

Quick start
===========

We can do this quickly.  Create a virtualenv and install django-oscar::

    mkvirtualenv --no-site-packages vanilla
    pip install -e git+git://github.com/tangentlabs/django-oscar.git#egg=django-oscar

Take a copy of the example vanilla site, and copy the quickstart settings into place::

    cp -r ~/.virtualenvs/myshop/lib/python2.6/site-packages/src/examples/vanilla/ /tmp/vanilla
    cd /tmp/vanilla
    cp settings_quickstart.py settings.py

Import the sample products and images::

    python manage.py import_catalogue ~/.virtualenvs/myshop/src/django-oscar/examples/sample-data/books-catalogue.csv
    python manage.py import_images ~/.virtualenvs/myshop/src/django-oscar/examples/sample-data/book-images.tar.gz

And there you have it: a fully functional ecommerce site with a product range of 100 popular books.

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

