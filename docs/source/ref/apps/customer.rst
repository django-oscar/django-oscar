========
Customer
========

The customer app includes models to record product alerts and sent emails.
It also contains the views that allow a customer to manage their data
(profile information, shipping addresses, etc.)

Abstract models
---------------

.. automodule:: oscar.apps.customer.abstract_models
    :members:

Forms
-----

.. automodule:: oscar.apps.customer.forms
    :members:

Views
-----

.. automodule:: oscar.apps.customer.views
    :members:

Alerts
------

The alerts module provides functionality that allows customers to sign up for
email alerts when out-of-stock products come back in stock. A form for signing
up is displayed on product detail pages when a product is not in stock.

If the ``OSCAR_EAGER_ALERTS`` setting is ``True``, then alerts are sent as soon
as affected stock records are updated. Alternatively, the management command
``oscar_send_alerts`` can be used to send alerts periodically.

The context for the alert email body contains a ``hurry`` variable that is set
to ``True`` if the number of active alerts for a product is greater than the
quantity of the product available in stock.

CustomerDispatcher
------------------

``oscar.apps.customer.utils.CustomerDispatcher`` is used to send customer emails
(e.g., registration, password reset, order confirmations).

AlertsDispatcher
----------------

``oscar.apps.customer.alerts.utils.AlertsDispatcher`` is used to send product alerts.
