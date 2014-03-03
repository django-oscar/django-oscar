==========
Promotions
==========

Promotions are small blocks of content that can link through to other parts of this site.
Examples include:

* A banner image shown on at the top of the homepage that links through to a new offer page
* A "pod" image shown in the right-hand sidebar of a page, linking through to newly merchandised
  page.
* A biography of an author (featuring an image and a block of HTML) shown at the top of the search
  results page when the search query includes the author's surname.

These are modeled using a base ``promotion`` model, which contains image fields, the link
destination, and two "linking" models which link promotions to either a page URL or a particular keyword.


Models
---------------

.. automodule:: oscar.apps.promotions.models
    :members:

Views
-----

.. automodule:: oscar.apps.promotions.views
    :members:
