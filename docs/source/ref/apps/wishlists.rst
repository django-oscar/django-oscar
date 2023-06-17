=========
Wishlists
=========

The wishlists app allows signed-in users to create one or more wishlists.  A
user can add a product to their wishlist from the product detail page and manage
their lists in the account section.

A wishlist can be private, public or shared. Private wishlist can only be seen by the owner of the wishlist, where public wishlists can be seen by anyone with the link. Shared wishlists have extra configuration, the owner of the wishlist can give access to multiple email addresses. The shared addresses will need an account on the webshop and need to be logged in in order to access the wishlist.

The wishlists app is wired up as a subapp of :doc:`customer` for the customer wish list related views.

Abstract models
---------------

.. automodule:: oscar.apps.wishlists.abstract_models
    :members:

Views
-----

.. automodule:: oscar.apps.customer.wishlists.views
    :members:
