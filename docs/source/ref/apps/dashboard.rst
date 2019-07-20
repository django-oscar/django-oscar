=========
Dashboard
=========

The dashboard is the backend interface for managing the store. That includes the
product catalogue, orders and stock, offers etc. It is intended as a
complete replacement of the Django admin interface.
The app itself only contains a view that serves as a kind of homepage, and
some logic for managing the navigation (in ``nav.py``). There's several sub-apps
that are responsible for managing the different parts of the Oscar store.

Permission-based dashboard
--------------------------
Staff users (users with ``is_staff==True``) get access to all views in the
dashboard. To better support Oscar's use for marketplace scenarios, the
permission-based dashboard has been introduced. If a non-staff user has
the ``partner.dashboard_access`` permission set, they are given access to a subset
of views, and their access to products and orders is limited.

:class:`~oscar.apps.partner.abstract_models.AbstractPartner` instances
have a :attr:`~oscar.apps.partner.abstract_models.AbstractPartner.users` field.
Prior to Oscar 0.6, this field was not used. Since Oscar 0.6, it is used solely
for modelling dashboard access.

If a non-staff user with the ``partner.dashboard_access`` permission is in
:attr:`~oscar.apps.partner.abstract_models.AbstractPartner.users`, they can:

* Create products. It is enforced that at least one stock record's partner has
  the current user in ``users``.
* Update products. At least one stock record must have the user in the stock
  record's partner's ``users``.
* Delete and list products. Limited to products the user is allowed to update.
* Managing orders. Similar to products, a user get access if one of an order's
  lines is associated with a matching partner. By default, user will get
  access to all lines of the order, even though supplies only one of them.
  If you need user to see only own lines or apply additional filtering - you
  can customise
  :meth:`~oscar.apps.dashboard.order.views.OrderDetailView.get_order_lines`
  method.

For many marketplace scenarios, it will make sense to ensure at checkout that
a basket only contains lines from one partner.
Please note that the dashboard currently ignores any other permissions,
including `Django's default permissions`_.

.. note::

  The permission-based dashboard currently does not support parent or child
  products. Supporting this requires a modelling change. If you require this,
  please get in touch so we can first learn about your use case.

.. _Django's default permissions: https://docs.djangoproject.com/en/stable/topics/auth/default/#default-permissions


Abstract models
---------------

None.

Views
-----

.. automodule:: oscar.apps.dashboard.views
    :members:
