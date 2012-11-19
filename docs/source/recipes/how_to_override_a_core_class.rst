============================
How to override a core class
============================

Example
-------

Suppose you want to alter the way order number's are generated.  By default,
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

the same module path as the one from oscar, that is, 

Discussion
----------

This principle of overriding classes from modules is an important feature of oscar
and makes it easy to customise virtually any functionality from the core.  For this
to work, you must ensure that:

1. You have a local version of the app, rather than using Oscar's directly
2. Your local class has the same module path relative to the app as the Oscar
   class being overridden

