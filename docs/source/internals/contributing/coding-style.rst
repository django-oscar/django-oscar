============
Coding Style
============

General
-------

Please follow these conventions while remaining sensible:

* `PEP8 -- Style Guide for Python Code <http://www.python.org/dev/peps/pep-0008/>`_
* `PEP257 -- Docstring Conventions <http://www.python.org/dev/peps/pep-0257/>`_
* `Django Coding Style <http://docs.djangoproject.com/en/stable/internals/contributing/writing-code/coding-style/>`_

`Code Like a Pythonista`_ is recommended reading.

flake8_ and isort_ are used to enforce basic coding standards. To run these
checks, use:

    $ make lint

.. _Code Like a Pythonista: http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html
.. _flake8: http://flake8.pycqa.org/en/latest/
.. _isort: http://timothycrosley.github.io/isort/

URLs
----

* List pages should use plurals; e.g. ``/products/``, ``/notifications/``

* Detail pages should simply be a PK/slug on top of the list page; e.g.
  ``/products/the-bible/``, ``/notifications/1/``

* Create pages should have 'create' as the final path segment; e.g.
  ``/dashboard/notifications/create/``

* URL names use dashes not underscores.

* Update pages are sometimes the same as detail pages (i.e., when in the
  dashboard).  In those cases, just use the detail convention, e.g.
  ``/dashboard/notifications/3/``.  If there is a distinction between the detail
  page and the update page, use ``/dashboard/notifications/3/update/``.

* Delete pages; e.g., ``/dashboard/notifications/3/delete/``

View class names
----------------

Classes should be named according to::

    '%s%sView' % (class_name, verb)

For example, ``ProductUpdateView``, ``OfferCreateView`` and
``PromotionDeleteView``.  This doesn't fit all situations, but it's a good basis.

Referencing managers
--------------------

Use ``_default_manager`` rather than ``objects``.  This allows projects to
override the default manager to provide domain-specific behaviour.

HTML
----

Please indent with four spaces.
