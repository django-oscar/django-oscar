============
Contributing
============

Some ground rules:

* To avoid disappointment, new features should be discussed on the mailing list
  (django-oscar@googlegroups.com) before serious work starts.

* Pull requests will be rejected if sufficient tests aren't provided.

* Please update the documentation when altering behaviour or introducing new features.

* Follow the conventions (see below).

Installation
============

From zero to tests passing in 2 minutes (most of which is PIL installing)::

    git clone git@github.com:<username>/django-oscar.git
    cd django-oscar
    mkvirtualenv oscar
    ./setup.py develop
    pip install -r requirements.txt
    ./run_tests.py

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
