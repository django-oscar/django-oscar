=========================
Template tags and filters
=========================

.. contents::
    :local:
    :depth: 2


Template filters
----------------

Currency filters
~~~~~~~~~~~~~~~~

Load these filters using ``{% load category_filters %}``.

.. autofunction:: oscar.templatetags.currency_filters.currency

Reviews filters
~~~~~~~~~~~~~~~

Load these tags using ``{% load reviews_filters %}``.

.. automodule:: oscar.templatetags.reviews_filters
   :members: as_stars, may_vote, is_review_permitted


Template tags
-------------

Basket tags
~~~~~~~~~~~

Load these tags using ``{% load basket_tags %}``.

.. autofunction:: oscar.templatetags.basket_tags.basket_form

Category tags
~~~~~~~~~~~~~

Load these tags using ``{% load category_tags %}``.

.. autofunction:: oscar.templatetags.category_tags.category_tree

Shipping tags
~~~~~~~~~~~~~

Load these tags using ``{% load shipping_tags %}``.

.. automodule:: oscar.templatetags.shipping_tags
   :members: shipping_charge, shipping_charge_discount, shipping_charge_excl_discount

Dashboard tags
~~~~~~~~~~~~~~

Load these tags using ``{% load dashboard_tags %}``.

.. automodule:: oscar.templatetags.dashboard_tags
   :members: num_orders, dashboard_navigation

Display tags
~~~~~~~~~~~~

Load these tags using ``{% load display_tags %}``.

.. automodule:: oscar.templatetags.display_tags
   :members: get_parameters, iffeature

Form tags
~~~~~~~~~

Load these tags using ``{% load form_tags %}``.

.. automodule:: oscar.templatetags.form_tags
   :members: annotate_form_field

History tags
~~~~~~~~~~~~

Load these tags using ``{% load history_tags %}``.

.. automodule:: oscar.templatetags.history_tags
   :members: recently_viewed_products, get_back_button

Product tags
~~~~~~~~~~~~

Load these tags using ``{% load product_tags %}``.

.. automodule:: oscar.templatetags.product_tags
   :members: render_product

Promotion tags
~~~~~~~~~~~~~~

Load these tags using ``{% load product_tags %}``.

.. automodule:: oscar.templatetags.promotion_tags
   :members: render_promotion

Purchase info tags
~~~~~~~~~~~~~~~~~~

Load these tags using ``{% load purchase_info_tags %}``.

.. automodule:: oscar.templatetags.purchase_info_tags
   :members: purchase_info_for_product, purchase_info_for_line

Sorting tags
~~~~~~~~~~~~

Load these tags using ``{% load sorting_tags %}``.

.. automodule:: oscar.templatetags.sorting_tags
   :members: anchor

String filters
~~~~~~~~~~~~~~

Load these filters using ``{% load string_filters %}``.

.. automodule:: oscar.templatetags.string_filters
   :members: split

Wishlist tags
~~~~~~~~~~~~~

Load these tags using ``{% load wishlist_tags %}``.

.. automodule:: oscar.templatetags.wishlist_tags
   :members: wishlists_containing_product
