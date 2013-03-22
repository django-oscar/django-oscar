============================
How to override a core class
============================

Much of Oscar's functionality is implemented using classes, when when a module
function might seem a better choice.  This is to allow functionality to be
customised.  Oscar uses a dynamic class loading mechanism that can be used to
override Oscar's core classes and use custom versions.

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

``INSTALLED_APPS`` tweak
------------------------

You will need to add your app that contains the overriding class to
``INSTALLED_APPS``, as well as let Oscar know that you're replacing the
corresponding core app with yours.  You can do that by supplying an extra
argument to ``get_core_apps`` function::

    # settings.py

    from oscar import get_core_apps
    # ...
    INSTALLED_APPS = [
        # all your apps in here as usual, EXCLUDING yourproject.order
    ] + get_core_apps(['yourproject.order'])

The ``get_core_apps`` function will replace ``oscar.apps.order`` with
``yourproject.order``.

Testing
-------

You can test whether your overriding worked by trying to get a class from your
module::

    >>> from oscar.core.loading import get_class
    >>> get_class('order.utils', 'OrderNumberGenerator')

Discussion
----------

This principle of overriding classes from modules is an important feature of Oscar
and makes it easy to customise virtually any functionality from the core.  For this
to work, you must ensure that:

1. You have a local version of the app, rather than using Oscar's directly
2. Your local class has the same module path relative to the app as the Oscar
   class being overridden

