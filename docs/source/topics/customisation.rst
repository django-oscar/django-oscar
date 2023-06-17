=================
Customising Oscar
=================

Many parts of Oscar can be adapted to your needs like any other Django
application:

* Many :doc:`settings</ref/settings>` control Oscar's behaviour
* The looks can be controlled by extending or overriding the
  :doc:`templates </howto/how_to_customise_templates>`

But as Oscar is built as a highly customisable and extendable framework, it
doesn't stop there. The behaviour of all Oscar apps can heavily be altered
by injecting your own code.

To extend the behaviour of an Oscar core app, it needs to be forked, which is
achieved with a simple management command. Afterwards, you should
generally be able to override any class/model/view by just dropping it
in the right place and giving it the same name.

In some cases, customising is slightly more involved. The following guides
give plenty of examples for specific use cases:

* :doc:`/howto/how_to_customise_models`
* :doc:`/howto/how_to_change_a_url`
* :doc:`/howto/how_to_customise_a_view`

For a deeper understanding of customising Oscar, the following documents are
recommended:

* :doc:`/internals/design-decisions`
* :doc:`Dynamic class loading</topics/class_loading_explained>`
* :doc:`fork_app`

.. _fork-oscar-app:

Fork the Oscar app
==================

If this is the first time you're forking an Oscar app, you'll need to create
a root module under which all your forked apps will live::

    $ mkdir yourappsfolder
    $ touch yourappsfolder/__init__.py

Now you call the helper management command which creates some basic files for
you. It is explained in detail in :doc:`fork_app`. Run it like this::

    $ ./manage.py oscar_fork_app order yourappsfolder
    Creating package yourappsfolder/order
    Creating admin.py
    Creating app config
    Creating models.py
    Creating migrations folder
    Replace the entry 'oscar.apps.order.apps.OrderConfig' with 'yourappsfolder.order.apps.OrderConfig' in INSTALLED_APPS


``oscar_fork_app`` has an optional third argument, which allows specifying
the sub-package name of the new app. For example, calling
``./manage.py oscar_fork_app order yourproject/ yoursubpackage.order`` places
the ``order`` app in the
``project_root/yourproject/yoursubpackage/order`` directory.

Replace Oscar's app with your own in ``INSTALLED_APPS``
=======================================================

You will need to let Django know that you replaced one of Oscar's core
apps. You can do that by replacing its entry in the ``INSTALLED_APPS`` setting,
with that for your own app.

.. note::

    Overrides of dashboard applications should follow overrides of core
    applications (basket, catalogue etc), since they depend on models,
    declared in the core applications. Otherwise, it could cause issues
    with Oscar's dynamic model loading.

    If you want to customise one of the dashboard applications, for instance
    ``yourappsfolder.dashboard.catalogue``, you also need to fork the core
    dashboard application ``yourappsfolder.dashboard``.

    Example:

    .. code:: django

        INSTALLED_APPS = [
            # all your non-Oscar apps
            ...
            # core applications
            'yourappsfolder.catalogue.apps.CatalogueConfig',
            'yourappsfolder.order.apps.OrderConfig',
            # dashboard applications
            'yourappsfolder.dashboard.apps.DashboardConfig',
            'yourappsfolder.dashboard.orders.apps.OrdersDashboardConfig',
            'yourappsfolder.dashboard.reports.apps.ReportsDashboardConfig',
        ]

.. note::

    It is recommended to use the dotted Python path to the app config class,
    rather than to the app package (e.g. ``yourappsfolder.order.apps.OrderConfig``
    instead of ``yourappsfolder.order``).

    This is to work around a `problem`_ in the way Django's automatic
    ``AppConfig`` discovery (introduced in version 3.2) scans for ``AppConfig``
    subclasses in an app's ``apps.py`` module (in short, it finds all
    ``AppConfig`` subclasses in the ``apps.py``, including ones imported to be
    subclassed). Specifying the path to the app config class ensures that
    automatic ``AppConfig`` discovery is not used at all.

.. _`problem`: https://code.djangoproject.com/ticket/33013

Start customising!
==================

You can now override every class (that is
:doc:`dynamically loaded </topics/class_loading_explained>`, which is
almost every class) in the app you've replaced. That means forms,
views, strategies, etc. All you usually need to do is give it the same name
and place it in a module with the same name.

Suppose you want to alter the way order numbers are generated.  By default,
the class ``oscar.apps.order.utils.OrderNumberGenerator`` is used. So just
create a class within your ``order`` app which
matches the module path from oscar: ``order.utils.OrderNumberGenerator``.  This
could subclass the class from Oscar or not::

    # yourproject/order/utils.py

    from oscar.apps.order.utils import OrderNumberGenerator as CoreOrderNumberGenerator


    class OrderNumberGenerator(CoreOrderNumberGenerator):

        def order_number(self, basket=None):
            num = super().order_number(basket)
            return "SHOP-%s" % num

To obtain an Oscar app's app config instance, look it up in the Django app
registry.
