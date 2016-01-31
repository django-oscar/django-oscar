==============================
How to set up order processing
==============================

How orders are processed differs for every shop.  Some shops will process orders
manually, using the dashboard to print picking slips and update orders once
items have shipped.  Others will use automated processes to send order details
to fulfillment partners and pick up shipment and cancellation messages.

Oscar provides only a skeleton for building your order processing pipeline on
top of.  This page details how it works and how to build your order processing
pipeline.

Structure
---------

There are two relevant Oscar apps to order processing.

* The checkout app is responsible for collecting the required shipping and
  payment information, taking payment in some sense and placing the order.  It
  is not normally used to process the order in any sense.  If your orders can be
  fulfilled immediately after being placed (eg digital products), it's better to
  use a separate process (like a cronjob or celery task).  That way, if the
  fulfilment work fails for some reason, it can be retried easily later.  It's
  also a neater decoupling of responsibilities.

* The order app has a ``processing.py`` module which is intended to handle order
  processing tasks, such as items being cancelled, shipped or returned.  More
  details below.

Modelling
---------

Oscar models order processsing through events.  There are three types to be
aware of:

* Shipping events.  These correspond to some change in the location or
  fulfilment status of the order items.  For instance, when items are shipped,
  returned or cancelled.  For digital goods, this would cover when items are
  downloaded.

* Payment events.  These model each transaction that relates to an order.  The
  payment model allows order lines to be linked to the payment event.

* Communication events. These capture emails and other messages sent to the
  customer about a particular order.  These aren't a core part of order
  processing and are used more for audit and to ensure, for example, that only
  one order confirmation email is sent to a customer.

Event handling
--------------

Most Oscar shops will want to customise the ``EventHandler`` class from the
order app.  This class is intended to handle all events and perform the
appropriate actions.  The main public API is

.. autoclass:: oscar.apps.order.processing.EventHandler
   :members: handle_shipping_event, handle_payment_event,
             handle_order_status_change
   :noindex:

Many helper methods are also provided:

.. autoclass:: oscar.apps.order.processing.EventHandler
   :members: validate_shipping_event, validate_payment_event,
             have_lines_passed_shipping_event, calculate_payment_event_subtotal,
             are_stock_allocations_available, consume_stock_allocations,
             cancel_stock_allocations, create_shipping_event,
             create_payment_event, create_communication_event, create_note
   :noindex:

Most shops can handle all their order processing through shipping events, which
may indirectly create payment events.

Customisation
-------------

Assuming your order processing involves an admin using the dashboard, then the
normal customisation steps are as follows:

#)  Ensure your orders are created with the right default status.
#)  Override the order dashboard's views and templates to provide the right
    interface for admins to update orders.
#)  Extend the ``EventHandler`` class to correctly handle shipping and payment
    events that are called from the dashboard order detail view.

It can be useful to use order and line statuses too.  Oscar provides some helper
methods to make this easier.

.. autoclass:: oscar.apps.order.abstract_models.AbstractOrder
   :members: pipeline, all_statuses, available_statuses, set_status
   :noindex:

.. autoclass:: oscar.apps.order.abstract_models.AbstractLine
   :members: pipeline, all_statuses, available_statuses, set_status
   :noindex:

Example
-------

Here is a reasonably common scenario for order processing.  Note that some of
the functionality described here is not in Oscar.  However, Oscar provides the
hook points to make implementing this workflow easy.

* An order is placed and the customer's bankcard is pre-authed for the order
  total.  The new order has status 'Pending'

* An admin logs into the dashboard and views all new orders.  They select the new
  order, retrieve the goods from the warehouse and get them ready to ship.

* When all items are retrieved, they select all the lines from the order and hit
  a button saying 'take payment'.  This calls the ``handle_payment_event``
  method of the ``EventHandler`` class which performs the settle transaction
  with the payment gateway and, if successful, creates a payment event against
  the order.

* If payment is successful, the admin ships the goods and gets a tracking number
  from the courier service.  They then select the shipped lines for the order and
  hit a button saying "mark as shipped".  This will show a form requesting a
  shipping number for the event.  When this is entered, the
  ``handle_shipping_event`` method of the ``EventHandler`` class is called,
  which will update stock allocations and create a shipping event.

