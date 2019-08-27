=============
Template tags
=============

Category tags
-------------

Load these tags using ``{% load category_tags %}``.

``category_tree``
~~~~~~~~~~~~~~~~~

Generates an annotated list of categories in a structure indented for easy
rendering of a nested tree in a single loop:

.. code-block:: html+django

    {% category_tree as tree_categories %}
    <ul>
    {% for category, info in tree_categories %}
        <li>
            <a href="{{ category.get_absolute_url }}">{{ category.name }}</a>
            {% if info.has_children %}
                <ul>
            {% else %}
                </li>
            {% endif %}
        {% for n in info.num_to_close %}
            </ul></li>
        {% endfor %}
    {% endfor %}
    </ul>

Each item in the list is a tuple of the form:

.. code-block:: python

    (
        category,
        {
            'has_children': True,   # Whether this node has children in the tree
            'level': 1,             # The depth of this node
            'num_to_close',         # A list indicating the number of leaf branches that
                                    # this category terminates.
        }
    )

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``depth``            The depth to which to fetch child categories
``parent``           The parent category for which to get a list of children
===================  =====================================================

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

``shipping_charge_excl_discount``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Injects the shipping charges with no discounts applied into the template context:

Usage:

.. code-block:: html+django

   {% shipping_charge_excl_discount shipping_method basket as name %}
   Shipping discount is {{ name }}.

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``shipping_method``  The shipping method instance
``basket``           The basket instance to calculate shipping charges for
``name``             The variable name to assign the charge to
===================  =====================================================

Image tags
----------

Load these tags using ``{% load image_tags %}``.

``oscar_thumbnail``
~~~~~~~~~~~~~~~~~~~

Returns the thumbnail URL for a source file.

.. code-block:: html+django

    <img src="{% oscar_thumbnail image.original '440x400' upscale=False %}" />

or places thumbnail object in the context, providing access to the properties of the
thumbnail such as the height and width.

.. code-block:: html+django

    {% oscar_thumbnail image.original "70x70" upscale=False as thumb %}
    <img src="{{ thumb.url }}" height="{{ thumb.height }}" width="{{ thumb.width }}">

Usage:

.. code-block:: html+django

    {% oscar_thumbnail [source] [size] [options] %}

or

.. code-block:: html+django

    {% oscar_thumbnail [source] [size] [options] as [variable] %}

When the ``OSCAR_THUMBNAIL_DEBUG`` setting is set to ``True``, this template tag will fail with an error if an exception is raised while generating the thumbnail. If set to ``False``, an empty string is returned.

The arguments are:

===================  =====================================================
Argument             Description
===================  =====================================================
``source``           Can be an ImageField, FileField, a file name (assuming default_storage), a URL.
``size``             Specified as :samp:`{width}x{height}`, :samp:`{width}x` or :samp:`x{height}`. Width and height are in pixels.
                     E.g. "70x120", "50x", "x155".
``options``          Space separated list of options which are used when processing the image to a thumbnail.
                     E.g. option ``upscale=False``.
===================  =====================================================


Datetime filters
-------------

Load these tags using ``{% load datetime_filters %}``.

``timedelta``
~~~~~~~~~~~~~~~~~

Returns a human-readable string representation of a time delta, in the current locale:

.. code-block:: html+django

    Time since creation: {{ basket.time_since_creation|timedelta }}

This renders something like:

.. code-block:: html

    Time since creation: 2 days


URL tags
-----------

Load these tags using ``{% load url_tags %}``.

``absolute_url``
~~~~~~~~~~~~~~~~~~

Returns an absolute URL for the provided domain and path.

.. code-block:: html+django

    <a href="{% absolute_url site.domain reset_url %}" class="btn-primary">Reset password</a>

This tag can be used with ``blocktrans`` as follows:

.. code-block:: html+django

    {% absolute_url site.domain reset_url as absolute_reset_url %}
    {% blocktrans with url=absolute_reset_url %}
        You can reset your password here - {{ url }}
    {% endblocktrans %}

The schema for absolute url can be set through ``OSCAR_URL_SCHEMA``
setting (``http`` by default).
