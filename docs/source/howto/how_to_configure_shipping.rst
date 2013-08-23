=========================
How to configure shipping
=========================

Configuring shipping is not trivial.  It generally requires creating a
'shipping' app within your project where you can define your own shipping
methods as well as a 'repository' class which determines when methods are
available.

This recipe explains in more detail how Oscar models shipping as well as the
steps involved in configuring shipping for your project.

How Oscar handles shipping charges
----------------------------------

Oscar uses a "repository" class to manage shipping charges.  The class is used
in two ways:

* _It provides a list of shipping methods available to the user._  This is used to
  generate the content for the shipping methods page of checkout, where the user
  can choose a shipping method.  The methods available generally depend on the
  user, the basket and the shipping address.

* _It allows a shipping method to be retrieved based on a identifying code._  When
  a user selects a shipping method during checkout, it is persisted in the
  session using a code.  This code is used to retrieve the chosen shipping
  method when it is required.

The default shipping repository `can be seen here`_.  It defaults to only
providing one shipping method, which has no charge.

.. note::

    Oscar's checkout process includes a page for choosing your shipping method.
    If there is only one method available for your basket then it will be chosen
    automatically and the user immediately redirected to the next step.

Custom shipping charges
-----------------------

In order to control shipping logic for your project, you need to define your own
repository class (see :doc:`how_to_override_a_core_class`).  It normally makes
sense to subclass the core ``Repository`` class and override the
``get_shipping_methods`` and ``find_by_code`` methods.

Here's a very simple example where all shipping costs are a fixed price,
irrespective of basket and shipping address::

    # myproject/shipping/repository.py

    from decimal import Decimal as D
    from oscar.apps.shipping import repository, methods as core_methods

    class Repository(repository.Repository):
        methods = [core_methods.FixedPrice(D('9.99'))]

        def get_shipping_methods(self, user, basket, shipping_addr=None, **kwargs):
            return self.prime_methods(basket, self.methods)

        def find_by_code(self, code, basket):
            for method in self.methods:
                if code == method.code:
                    return self.prime_method(basket, method)

Note that both these methods must return 'primed' method instances, which means
the basket instance has been injected into the method.  This allows the method
instance to return the shipping charge directly without requiring the basket to
be passed again (which is useful in templates).

As you can see the ``get_shipping_methods`` can depend on several things:

* the user in question (e.g., staff get cheaper shipping rates)
* the basket (e.g., shipping is charged based on the weight of the basket)
* the shipping address (e.g., overseas shipping is more expensive)

Here's a more involved example repository that has two fixed price charges::

    # myproject/shipping/repository.py

    from decimal import Decimal as D
    from oscar.apps.shipping import repository, methods as core_methods

    # We create subclasses so we can give them different codes and names
    class Standard(core_methods.FixedPrice):
        code = 'standard'
        name = _("Standard shipping")

    class Express(core_methods.FixedPrice):
        code = 'express'
        name = _("Express shipping")

    class Repository(repository.Repository):
        methods = [Standard(D('10.00')), Express(D('20.00'))]

        def get_shipping_methods(self, user, basket, shipping_addr=None, **kwargs):
            return self.prime_methods(basket, self.methods)

        def find_by_code(self, code, basket):
            for method in self.methods:
                if code == method.code:
                    return self.prime_method(basket, method)

.. _`can be seen here`: https://github.com/tangentlabs/django-oscar/blob/master/oscar/apps/shipping/repository.py

Shipping methods
----------------

The repository class is responsible for return shipping method instances.  Oscar
defines several of these but it is easy to write your own, their interface is
simple.

The base shipping method class ``oscar.apps.shipping.base.ShippingMethod`` (that
all shipping methods should subclass has API:

.. autoclass:: oscar.apps.shipping.base.ShippingMethod
    :members:

Core shipping methods
~~~~~~~~~~~~~~~~~~~~~

The shipping methods that ship with Oscar are:

* ``oscar.apps.shipping.methods.Free``.  No shipping charges.

* ``oscar.apps.shipping.methods.WeightBased``.  This is a model-driven method
  that uses two models: ``WeightBased`` and ``WeightBand`` to provide charges
  for different weight bands.  By default, the method will calculate the weight
  of a product by looking for a 'weight' attribute although this can be
  configured.  

* ``oscar.apps.shipping.methods.FixedPrice``.  This simply charges a fixed price for 
  shipping, irrespective of the basket contents.

* ``oscar.apps.shipping.methods.OrderAndItemCharges``.  This is a model which
  specifies a per-order and a per-item level charge.

To apply your domain logic for shipping, you will need to override
the default repository class (see :doc:`how_to_override_a_core_class`) and alter
the implementation of the ``get_shipping_methods`` method.  This method
should return a list of "shipping method" classes already instantiated
and holding a reference to the basket instance.

Building a custom shipping method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At a minimum, a custom shipping method class should define a ``code`` and
``name`` attribute to distinguish it from other methods.  It is also normal to
override the ``basket_charge_incl_tax`` and ``basket_charge_excl_tax`` methods
to implement your custom shipping charge logic.

.. tip::

    Most of the shipping logic should live in the repository class, the method
    instance is only responsble for returning the charge for a given basket.
