============================
How to override a core class
============================

This How-to describes how Oscar's dynamic class loading mechanism can be used
to override Oscar's core classes and use custom versions.

It builds upon the steps described in :doc:`/topics/customisation`. Please
read it first and ensure that you've:

* Created a Python module with the the same label
* Added it as Django app to ``INSTALLED_APPS``

Example
-------

Suppose you want to alter the way order numbers are generated.  By default,
the class ``oscar.apps.order.utils.OrderNumberGenerator`` is used.  To change
the behaviour, you need to ensure that you have a local version of the
``order`` app (i.e., ``INSTALLED_APPS`` should contain ``yourproject.order``, not
``oscar.apps.order``).  Then create a class within your ``order`` app which
matches the module path from oscar: ``order.utils.OrderNumberGenerator``.  This
could subclass the class from oscar or not.  An example implementation is::

    # yourproject/order/utils.py

    from oscar.apps.order.utils import OrderNumberGenerator as CoreOrderNumberGenerator


    class OrderNumberGenerator(CoreOrderNumberGenerator):

        def order_number(self, basket=None):
            num = super(OrderNumberGenerator, self).order_number(basket)
            return "SHOP-%s" % num


You will need to add your app that contains the overriding class to
``INSTALLED_APPS``, as well as let Oscar know that you're replacing the
corresponding core app with yours.  You can do that by supplying an extra
argument to ``get_core_apps`` function.

