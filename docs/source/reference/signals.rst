=======
Signals
=======

Oscar implements a number of custom signals that provide useful hook-points for
adding functionality.

product_viewed
--------------

.. data:: oscar.apps.catalogue.signals.product_viewed
    :class:

Raised when a product detail page is viewed.

Arguments sent with this signal:

``product``
    The product being viewed

``user``
    The user in question

``request``
    The request instance

``response``
    The response instance

product_search
--------------

.. data:: oscar.apps.catalogue.signals.product_search
    :class:

Raised when a search is performed.

Arguments sent with this signal:

``query``
    The search term

``user``
    The user in question

basket_addition
---------------

.. data:: oscar.apps.basket.signals.basket_addition
    :class:

Raised when a product is added to a basket

Arguments sent with this signal:

``product``
    The product being added

``user``
    The user in question

voucher_addition
----------------

.. data:: oscar.apps.basket.signals.voucher_addition
    :class:

Raised when a valid voucher is added to a basket

Arguments sent with this signal:

``basket``
    The basket in question

``voucher``
    The voucher in question

pre_payment
-----------

.. data:: oscar.apps.checkout.signals.pre_payment
    :class:

Raised immediately before attempting to take payment in the checkout.

Arguments sent with this signal:

``view``
    The view class instance

post_payment
------------

.. data:: oscar.apps.checkout.signals.post_payment
    :class:

Raised immediately after payment has been taken.

Arguments sent with this signal:

``view``
    The view class instance

order_placed
------------

.. data:: oscar.apps.order.signals.order_placed
    :class:

Raised by the :class:`oscar.apps.order.utils.OrderCreator` class when creating an order.

Arguments sent with this signal:

``order``
    The order created

``user``
    The user creating the order (not necessarily the user linked to the order
    instance!)

review_created
--------------

.. data:: oscar.apps.catalogue.reviews.signals.review_added
    :class:

Raised when a product detail page is viewed.

Arguments sent with this signal:

``review``
    The review that was created

``user``
    The user performing the action

``request``
    The request instance

``response``
    The response instance
