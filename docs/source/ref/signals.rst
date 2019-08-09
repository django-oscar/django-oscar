=======
Signals
=======

Oscar implements a number of custom signals_ that provide useful hook-points
for adding functionality.

.. _signals: https://docs.djangoproject.com/en/stable/topics/signals/

``product_viewed``
------------------

.. class:: oscar.apps.catalogue.signals.product_viewed

    Raised when a product detail page is viewed.

Arguments sent with this signal:

.. attribute:: product

    The product being viewed

.. attribute:: user

    The user in question

.. attribute:: request

    The request instance

.. attribute:: response

    The response instance

``product_search``
------------------

.. class:: oscar.apps.catalogue.signals.product_search

   Raised when a search is performed.

Arguments sent with this signal:

.. attribute:: query

    The search term

.. attribute:: user

    The user in question

.. _user_registered_signal:

``user_registered``
-------------------

.. class:: oscar.apps.customer.signals.user_registered

   Raised when a user registers

Arguments sent with this signal:

.. attribute:: request

    The request instance

.. attribute:: user

    The user in question

.. _basket_addition_signal:

``basket_addition``
-------------------

.. class:: oscar.apps.basket.signals.basket_addition

   Raised when a product is added to a basket

Arguments sent with this signal:

.. attribute:: request

    The request instance

.. attribute:: product

    The product being added

.. attribute:: user

    The user in question

``voucher_addition``
--------------------

.. class:: oscar.apps.basket.signals.voucher_addition

   Raised when a valid voucher is added to a basket

Arguments sent with this signal:

.. attribute:: basket

    The basket in question

.. attribute:: voucher

    The voucher in question

.. _start_checkout_signal:

``start_checkout``
------------------

.. class:: oscar.apps.checkout.signals.start_checkout

   Raised when the customer begins the checkout process

Arguments sent with this signal:

.. attribute:: request

    The request instance

``pre_payment``
---------------

.. class:: oscar.apps.checkout.signals.pre_payment

   Raised immediately before attempting to take payment in the checkout.

Arguments sent with this signal:

.. attribute:: view

    The view class instance

``post_payment``
----------------

.. class:: oscar.apps.checkout.signals.post_payment

   Raised immediately after payment has been taken.

Arguments sent with this signal:

.. attribute:: view

    The view class instance

``order_placed``
----------------

.. class:: oscar.apps.order.signals.order_placed

   Raised by the :class:`oscar.apps.order.utils.OrderCreator` class when
   creating an order.

Arguments sent with this signal:

.. attribute:: order

    The order created

.. attribute:: user

    The user creating the order (not necessarily the user linked to the order
    instance!)

``post_checkout``
-----------------

.. class:: oscar.apps.checkout.signals.post_checkout

    Raised by the :class:`oscar.apps.checkout.mixins.OrderPlacementMixin` class
    when a customer completes the checkout process

.. attribute:: order

    The order created

.. attribute:: user

    The user who completed the checkout

.. attribute:: request

    The request instance

.. attribute:: response

    The response instance

``review_created``
------------------

.. class:: oscar.apps.catalogue.reviews.signals.review_added

    Raised when a review is added.

Arguments sent with this signal:

.. attribute:: review

    The review that was created

.. attribute:: user

    The user performing the action

.. attribute:: request

    The request instance

.. attribute:: response

    The response instance
