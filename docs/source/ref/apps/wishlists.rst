=========
Wishlists
=========

The wishlists app allows signed-in users to create one or more wishlists.  A
user can add a product to their wishlist from the product detail page and manage
their lists in the account section.

The wishlists app is wired up as a subapp of :doc:`customer`.

.. note::

    Please note that currently only private wishlists are supported. The hooks
    and fields for public (as in general public) and shared (as in access via an
    obfuscated link) are there, but the UI hasn't been designed yet.

Abstract models
---------------

.. automodule:: oscar.apps.wishlists.abstract_models
    :members:

Views
-----

.. automodule:: oscar.apps.customer.wishlists.views
    :members:
