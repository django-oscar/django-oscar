============================================
Django-Oscar - Flexible e-commerce on Django
============================================

*django-oscar* is an e-commerce framework for Django 1.3 designed for building
domain-driven e-commerce sites.  It is structured such that any part of the
core functionality can be customised to suit the needs of your project.  This
allows it to handle a wide range of e-commerce sites, from large-scale B2C
sites to complex B2B sites rich in domain-specific business logic.

`Read the docs`_

.. _`Read the docs`: http://django-oscar.readthedocs.org/en/latest/

Features
--------

* Extensible core - any class can be overridden, replaced and extended
* Well-designed set of models based on the experiece of many e-commerce
  projects, of both large- and small-scale.
* Dashboard for product, order and offer management.
* Highly sophisticated offers and vouchers system, supporting virtually any offer type
  you can think of.
* Support for split-payment orders, complicated order fulfilment pipelines
* Anonymous checkout
* Extensive test suite - we love testing!

Quick start
-----------

After forking, do the following::

    mkvirtualenv oscar
    git clone git@github.com/<username>/django-oscar.git
    cd django-oscar
    python setup.py develop
    pip install -r testing-reqs.txt

You can run the test suite using::
        
    ./run_tests.py

You can browse a "sandbox" shop by doing the following::

    cd sandbox
    ./manage.py syncdb --noinput
    ./manage.py import_catalogue data/books-catalogue.csv
    ./manage.py import_images data/book-images.tar.gz
    ./manage.py runserver

Contributors
------------

* David Winterbottom (`@codeinthehole`_)
* Andrew Ingram (`@AndrewIngram`_)
* `Mirumee`_

Oscar is used and maintained by `Tangent Labs`_, a London-based digital agency

.. _`@codeinthehole`: https://twitter.com/codeinthehole
.. _`@AndrewIngram`: https://twitter.com/AndrewIngram
.. _`Mirumee`: http://mirumee.com
.. _`Tangent Labs`: http://www.tangentlabs.co.uk

Plugins
-------

The following libraries complement and extend oscar:

* `django-oscar-datacash`_ - integration module with the payment gateway, DataCash

.. _`django-oscar-datacash`: https://github.com/tangentlabs/django-oscar-datacash

More to come!

More information
----------------

Follow `@codeinthehole`_ on twitter.  Mailing list and IRC to come.

.. _`@codeinthehole`: https://twitter.com/codeinthehole

Changelog
---------

0.1
~~~

* Initial release - used in production by two major applications at Tangent
* Still a bit rough around the edges
* Docs are a bit stale and need updating in 0.2

Roadmap
-------

0.2
~~~

* Much better documentation, including recipes for common tasks
* Refactoring of shipping methods
* New dashboard functionality for product management, order management, customer services
