=========================
Template tags and filters
=========================

.. contents::
    :local:
    :depth: 1

Basket tags
-----------

Load these tags using ``{% load basket_tags %}``.

``basket_form``
~~~~~~~~~~~~~~~

Injects a add-to-basket form into the template context:

Usage:

.. code-block:: html+django

   {% basket_form request product as name %}

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``request``          The request instance
``product``          A product instance
``name``             The variable name to assign to
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=basket_form+path%3A%2Foscar%2Ftemplates&type=Code

Category tags
-------------

Load these tags using ``{% load category_tags %}``.

``category_tree``
~~~~~~~~~~~~~~~~~

Injects a category tree into the template context:

Usage:

.. code-block:: html+django

   {% category_tree [depth] [parent] as name %}

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``depth``            How deep within the tree to fetch
``parent``           The root category instance
``name``             The variable name to assign to
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=category_tree+path%3A%2Foscar%2Ftemplates&type=Code

Currency filters
----------------

Load these filters using ``{% load category_filters %}``.

``currency``
~~~~~~~~~~~~

Format a decimal value as a currency

For example:

.. code-block:: html+django

   {{ total|currency:"GBP" }}

or using the core :class:`~oscar.core.prices.Price` class:

.. code-block:: html+django

   {{ price.incl_tax|currency:price.currency }}

If the arg is committed, then the currency is taken from the
``OSCAR_DEFAULT_CURRENCY`` setting.

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=currency+path%3A%2Foscar%2Ftemplates&type=Code

Shipping tags
-------------

Load these tags using ``{% load shipping_tags %}``.

``shipping_charge``
~~~~~~~~~~~~~~~~~~~

Injects the shipping charge into the template context:

Usage:

.. code-block:: html+django

   {% shipping_charge shipping_method basket as name %}
   Shipping charge is {{ name }}.

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``shipping_method``  The shipping method instance
``basket``           The basket instance to calculate shipping charges for
``name``             The variable name to assign the charge to
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=shipping_charge+path%3A%2Foscar%2Ftemplates&type=Code

``shipping_charge_discount``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Injects the shipping discount into the template context:

Usage:

.. code-block:: html+django

   {% shipping_discount shipping_method basket as name %}
   Shipping discount is {{ charge }}.

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``shipping_method``  The shipping method instance
``basket``           The basket instance to calculate shipping charges for
``name``             The variable name to assign the charge to
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=shipping_discount+path%3A%2Foscar%2Ftemplates&type=Code

``shipping_charge_excl_discount``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Injects the shipping charge with no discounts applied into the template context:

Usage:

.. code-block:: html+django

   {% shipping_charge_excl_discount shipping_method basket as name %}
   Shipping discount is {{ name }}.

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``shipping_method``  The shipping method instance
``basket``           The basket instance to calculate shipping charge for
``name``             The variable name to assign the charge to
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=shipping_charge_excl_discount+path%3A%2Foscar%2Ftemplates&type=Code

Dashboard tags
--------------

Load these tags using ``{% load dashboard_tags %}``.

``num_orders``
~~~~~~~~~~~~~~

Renders the number of orders a given user has placed.

Usage:

.. code-block:: html+django

   Number of orders placed: {% num_orders user %}

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``user``             The user instance
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=num_orders+path%3A%2Foscar%2Ftemplates&type=Code

``dashboard_navigation``
~~~~~~~~~~~~~~~~~~~~~~~~

Injects the dashboard navigation nodes into the template context using name
``nav_items``

Usage:

.. code-block:: html+django

   {% dashboard_navigation user %}

   <ul>
       {% for item in nav_items %}
       <li>
           {% if item.is_heading %}
                ...
           {% else %}
               ...
           {% endif %}
       </li>
   </ul>

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``user``             The user instance
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=dashboard_navigation+path%3A%2Foscar%2Ftemplates&type=Code

Display tags
------------

Load these tags using ``{% load display_tags %}``.

``get_parameters``
~~~~~~~~~~~~~~~~~~

Renders the query parameters with the exception of the passed one

Usage:

.. code-block:: html+django

   <a href="?{% get_parameters key %}&key=1">...</a>

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``key``              The query param to ignore
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=get_parameters+path%3A%2Foscar%2Ftemplates&type=Code

``iffeature``
~~~~~~~~~~~~~

Only renders the contained mark-up if the specified feature is enabled.

Usage:

.. code-block:: html+django

   {% iffeature feature_name %}
       ...
   {% endiffeature %}

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``feature_name``     The feature name to test for
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=get_parameters+path%3A%2Foscar%2Ftemplates&type=Code

Form tags
---------

Load these tags using ``{% load form_tags %}``.

``annotate_form_field``
~~~~~~~~~~~~~~~~~~~~~~~

Sets a ``widget_type`` attribute on a form field so templates can handle
widgets differently.

Usage:

.. code-block:: html+django

   {% annotate_form_field field %}

   {% if field.widget_type == 'CheckboxInput %}
       ...
   {% endif %}

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``field``            The form field to annotate
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=annotate_form_field+path%3A%2Foscar%2Ftemplates&type=Code

History tags
------------

Load these tags using ``{% load history_tags %}``.

``recently_viewed_products``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Include a list of the customer's recently viewed products.

Usage:

.. code-block:: html+django

   {% recently_viewed_products %}

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=recently_viewed_products+path%3A%2Foscar%2Ftemplates&type=Code

``get_back_button``
~~~~~~~~~~~~~~~~~~~

Assign a dict of data for rendering a button that takes the user to the
previous page (if on same site).

Usage:

.. code-block:: html+django

   {% get_back_button as back_button %}

   {% if back_button %}
       <a href="{{ back_button.url }}">{{ back_button.title }}</a>
   {% endif %}

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=get_back_button+path%3A%2Foscar%2Ftemplates&type=Code

Product tags
------------

Load these tags using ``{% load product_tags %}``.

``render_product``
~~~~~~~~~~~~~~~~~~

Render a product HTML snippet for inclusion in a browsing page (like search
results or category browsing).

Usage:

.. code-block:: html+django

   {% render_product product %}

===================  =====================================================
Argument             Description
===================  =====================================================
``product``          The product instance to render
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=render_product+path%3A%2Foscar%2Ftemplates&type=Code


Promotion tags
--------------

Load these tags using ``{% load product_tags %}``.

``render_promotion``
~~~~~~~~~~~~~~~~~~~~

Render a promotion HTML snippet.

Usage:

.. code-block:: html+django

   {% render_product promotion %}

===================  =====================================================
Argument             Description
===================  =====================================================
``promotion``        The promotion instance to render
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=render_promotion+path%3A%2Foscar%2Ftemplates&type=Code


Purchase info tags
------------------

Load these tags using ``{% load purchase_info_tags %}``.

``purchase_info_for_product``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return the ``PurchaseInfo`` instance for a given product.

Usage:

.. code-block:: html+django

   {% purchase_info_for_product request product as name %}

===================  =====================================================
Argument             Description
===================  =====================================================
``request``          The request instance
``product``          The product instance
``name``             The variable name to assign to
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=purchase_info_for_product+path%3A%2Foscar%2Ftemplates&type=Code

``purchase_info_for_line``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Return the ``PurchaseInfo`` instance for a given basket line.

Usage:

.. code-block:: html+django

   {% purchase_info_for_line request line as name %}

===================  =====================================================
Argument             Description
===================  =====================================================
``request``          The request instance
``line``             The basket line instance
``name``             The variable name to assign to
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=purchase_info_for_line+path%3A%2Foscar%2Ftemplates&type=Code


Reviews filters
---------------

Load these tags using ``{% load reviews_tags %}``.

``as_stars``
~~~~~~~~~~~~

Convert a numeric value to a text version (for use in CSS).

Usage:

.. code-block:: html+django

   {{ 5|as_stars }}

This will render "Five". More common usage:

.. code-block:: html+django

   {{ product.rating|as_stars }}

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=as_stars+path%3A%2Foscar%2Ftemplates&type=Code

``may_vote``
~~~~~~~~~~~~

Returns a boolean indicating if a given user can vote on a review.

Usage:

.. code-block:: html+django

   {% if review|may_vote:user %}
       ...
   {% endif %}

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=may_vote+path%3A%2Foscar%2Ftemplates&type=Code

``is_review_permitted``
~~~~~~~~~~~~~~~~~~~~~~~

Returns a boolean indicating if a given user may review a given product.

Usage:

.. code-block:: html+django

   {% if product|is_review_permitted:user %}
       ...
   {% endif %}

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=is_review_permitted+path%3A%2Foscar%2Ftemplates&type=Code


Sorting tags
------------

Load these tags using ``{% load sorting_tags %}``.

``anchor``
~~~~~~~~~~

Render an anchor tag with the appropriate ``href`` attribute for sorting on a given field.

Usage:

.. code-block:: html+django

   {% anchor query_param title %}

===================  =====================================================
Argument             Description
===================  =====================================================
``query_param``      The query parameter to use with key ``sort`` in the 
                     generated URL.
``title``            The text to include in the anchor tag.
===================  =====================================================

For example, on URL ``/dashboard/orders/``, including:

.. code-block:: html+django

   {% anchor 'number' _("Order number") %}

will render:

.. code-block:: html+django

   <a href="/dashboard/orders/?sort=number">Order number</a>

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=anchor+path%3A%2Foscar%2Ftemplates&type=Code


String filters
--------------

Load these filters using ``{% load string_filters %}``.

``split``
~~~~~~~~~

Return a string split by the passed separator character (which defaults to
space).

Example usage:

.. code-block:: html+django

   {% for tag in message.tags|split %}{{ tag }}{% endfor %}

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=split+path%3A%2Foscar%2Ftemplates&type=Code


Wishlist tags
-------------

Load these tags using ``{% load wishlist_tags %}``.

``wishlists_containing_product``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inject the wishlists that contain a given product into the template context.

Usage:

.. code-block:: html+django

   {% wishlists_containing_product wishlists product as name %}

===================  =====================================================
Argument             Description
===================  =====================================================
``wishlists``        An iterable of wishlist instances.
``product``          The product to test for.
``name``             The variable name to assign to
===================  =====================================================

`Example usage in Oscar's templates`__

__ https://github.com/tangentlabs/django-oscar/search?q=wishlists_containing_product+path%3A%2Foscar%2Ftemplates&type=Code
