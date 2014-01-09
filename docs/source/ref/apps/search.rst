======
Search
======

Oscar provides a search view that extends Haystack's ``FacetedSearchView`` to
provide better support for faceting.  

* Facets are configured using the ``OSCAR_SEARCH_FACETS`` setting, which is
  used to configure the ``SearchQuerySet`` instance within the search
  application class.

* A simple search form is injected into each template context using a context
  processor ``oscar.apps.search.context_processors.search_form``.

Views
-----

.. automodule:: oscar.apps.search.views
    :members:

Forms
-----

.. automodule:: oscar.apps.search.forms
    :members:

Utils
-----

.. automodule:: oscar.apps.search.facets
    :members:
