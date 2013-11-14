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
the ``partner.dashboard_access`` permission set, she is given access to a subset
of views, and her access to products and orders is limited.

:class:`~oscar.apps.partner.abstract_models.AbstractPartner` instances
have a :attr:`~oscar.apps.partner.abstract_models.AbstractPartner.users` field.
If a non-staff user is in that list, she is given
access to associated models. By default, this access is rather permissive:
a user gets granted access if one of a product's stock records has a matching
partner, or if one of an order's lines is associated with a matching partner.

For many marketplace scenarios, it will make sense to ensure at checkout that
a basket only contains lines from one partner.

Abstract models
---------------

None.

Views
-----

.. automodule:: oscar.apps.dashboard.views
    :members:

