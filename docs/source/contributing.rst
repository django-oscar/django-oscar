============
Contributing
============

Some ground rules:

* To avoid disappointment, new features should be discussed on the mailing list
  (django-oscar@googlegroups.com) before serious work starts. 

* Pull requests will be rejected if sufficient tests aren't provided.

* Make pull requests against Oscar's master branch unless instructed otherwise.

* Please update the documentation when altering behaviour or introducing new features.

* Follow the conventions (see below).

Installation
============

After forking, run::

    git clone git@github.com:<username>/django-oscar.git
    cd django-oscar
    mkvirtualenv oscar  # optional but recommended
    make install

Running tests
=============

Oscar uses a nose_ testrunner which can be invoked using::

.. _nose: http://nose.readthedocs.org/en/latest/

    ./runtests.py

To run a subset of tests, you can use filesystem or module paths.  These two
commands will run the same set of tests::

    ./runtests.py tests/unit/order
    ./runtests.py tests.unit.order

To run an individual test class use one of::

    ./runtests.py tests/unit/order:TestSuccessfulOrderCreation
    ./runtests.py tests.unit.order:TestSuccessfulOrderCreation

(Note the ':'.)

To run an individual test, use one of::

    ./runtests.py tests/unit/order:TestSuccessfulOrderCreation.test_creates_order_and_line_models
    ./runtests.py tests.unit.order:TestSuccessfulOrderCreation.test_creates_order_and_line_models

Oscar's testrunner uses the progressive_ plugin when running all tests, but uses
the spec_ plugin when running a subset.  It is a good practice to name your test
cases and methods so that the spec output reads correctly.

.. _progressive: http://pypi.python.org/pypi/nose-progressive/
.. _spec: http://darcs.idyll.org/~t/projects/pinocchio/doc/#spec-generate-test-description-from-test-class-method-names

Playing in the sandbox
======================

Oscar ships with a 'sandbox' site which can be run locally to play around with
Oscar using a browser.  Set it up by::

   make sandbox 
   cd sites/sandbox 
   ./manage.py runserver

This will create the database and load some fixtures.

Writing docs
============

There's a helper script for building the docs locally::

    cd docs
    ./test_docs.sh

Conventions
===========

General
-------

* PEP8 everywhere while remaining sensible

URLs
----

* List pages should use plurals, eg ``/products/``, ``/notifications/``

* Detail pages should simply be a PK/slug on top of the list page, eg
  ``/products/the-bible/``, ``/notifications/1/``
  
* Create pages should have 'create' as the final path segment, eg
  ``/dashboard/notifications/create/``

* Update pages are sometimes the same as detail pages (ie when in the
  dashboard).  In those cases, just use the detail convention, eg
  ``/dashboard/notifications/3/``.  If there is a distinction between the detail
  page and the update page, use ``/dashboard/notifications/3/update/``.

* Delete pages, eg /dashboard/notifications/3/delete/

View class names
----------------

Classes should be named according to::

    '%s%sView' % (class_name, verb)

For example, ``ProductUpdateView``, ``OfferCreateView`` and
``PromotionDeleteView``.  This doesn't fit all situations but it's a good basis.
