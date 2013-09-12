=========
Wishlists
=========

The wishlists app is built to allow a user create one or more wishlists and let
her add products to one or more of her wishlists. She can add a product from the
product's detail page and manage the lists in the account section.

The wishlists app is hence wired up as a subapp of :doc:`customer` and a partial
is included in `add_to_basket_form.html`.

Please note that currently only private wishlists are supported. The
hooks and fields for public (as in general public) and shared (as in access via
an obfuscated link) are there, but the UI hasn't been designed yet.


Abstract models
---------------

.. automodule:: oscar.apps.wishlists.abstract_models
    :members:

Views
-----

.. automodule:: oscar.apps.customer.wishlists.views
    :members:
