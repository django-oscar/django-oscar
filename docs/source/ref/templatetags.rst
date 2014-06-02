=============
Template tags
=============

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
