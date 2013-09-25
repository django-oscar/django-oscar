=========
Dashboard
=========

The dashboard is the backend interface for managing the store. That includes the
product catalogue, orders and stock, offers etc. It is intended as a
complete replacement of the Django admin interface.
The app itself only contains a view that serves as a kind of homepage, and
some logic for managing the navigation (in ``nav.py``). There's several sub-apps
that are responsible for managing the different parts of the Oscar store.

Abstract models
---------------

None.

Views
-----

.. automodule:: oscar.apps.dashboard.views
    :members:

