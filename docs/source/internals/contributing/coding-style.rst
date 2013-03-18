============
Coding Style
============

General
-------

* PEP8 everywhere while remaining sensible

URLs
----

* List pages should use plurals; e.g. ``/products/``, ``/notifications/``

* Detail pages should simply be a PK/slug on top of the list page; e.g.
  ``/products/the-bible/``, ``/notifications/1/``
  
* Create pages should have 'create' as the final path segment; e.g.
  ``/dashboard/notifications/create/``

* Update pages are sometimes the same as detail pages (i.e., when in the
  dashboard).  In those cases, just use the detail convention, eg
  ``/dashboard/notifications/3/``.  If there is a distinction between the detail
  page and the update page, use ``/dashboard/notifications/3/update/``.

* Delete pages; e.g., ``/dashboard/notifications/3/delete/``

View class names
----------------

Classes should be named according to::

    '%s%sView' % (class_name, verb)

For example, ``ProductUpdateView``, ``OfferCreateView`` and
``PromotionDeleteView``.  This doesn't fit all situations, but it's a good basis.