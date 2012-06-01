=======
Signals
=======

Oscar defined a number of custom signals that provide useful hook-points for
adding functionality.

order_placed
------------

.. data:: oscar.apps.order.order_placed
    :class:

Raised by the :class:`oscar.apps.order.OrderCreator` class when creating an order.

Arguments sent with this signal:

``order``
    The order created

``user``
    The user creating the order (not necessarily the user linked to the order
    instance!)
