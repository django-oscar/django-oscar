==============================================
How to add views or change URLs or permissions
==============================================

Oscar has many views and associated URLs.  Often you want to customise these
URLs for your domain, or add additional views to an app.

This how-to describes how to do just that.
It builds upon the steps described in :doc:`/topics/customisation`. Please
read it first and ensure that you've:

* Created a Python module with the the same label
* Added it as Django app to ``INSTALLED_APPS``
* Added a ``models.py`` and ``admin.py``

The application class
---------------------

Each Oscar app comes with an application instance which inherits from
:class:`oscar.core.application.Application`. They're mainly used to gather
URLs (with the correct permissions) for each Oscar app. This structure makes
Oscar apps more modular as each app is responsible for its own URLs. And as
it is a class, it can be overridden like any other Oscar class; hence making
it straightforward to change URLs or add new views.
Each app instance exposes a ``urls`` property, which is used to access the
list of URLs of an app.

The application tree
--------------------

Oscar's app instances are organised in a tree structure. The root application
illustrates this nicely::

    # oscar/app.py
    class Shop(Application):
        name = None

        catalogue_app = get_class('catalogue.app', 'application')
        basket_app = get_class('basket.app', 'application')
        # ...

        def get_urls(self):
            urls = [
                url(r'^catalogue/', include(self.catalogue_app.urls)),
                url(r'^basket/', include(self.basket_app.urls)),
                # ...
            ]

The root app pulls in the URLs from its children. That means to add
all Oscar URLs to your Django project, you only need to include the ``urls``
property from the root app::

    # urls.py
    from oscar.app import application

    urlpatterns = [
        # Your other URLs
        url(r'', include(application.urls)),
    ]

Changing sub app
----------------

Sub-apps such as the ``catalogue`` app are loaded dynamically, just as most
other classes in Oscar::

    # oscar/app.py
    class Shop(Application):
        name = None

        catalogue_app = get_class('catalogue.app', 'application')
        customer_app = get_class('customer.app', 'application')
        # ...

That means you just need to create another
``application`` instance. It will usually inherit from Oscar's version. Say
you'd want to add another view to the promotions app. You only need to
create a class called ``PromotionsApplication`` (and usually inherit from
Oscar's version) and add your view::

    # yourproject/promotions/app.py

    from oscar.apps.promotions.app import PromotionsApplication as CorePromotionsApplication
    from .views import MyExtraView

    class PromotionsApplication(CorePromotionsApplication):
        extra_view = MyExtraView

    application = PromotionsApplication()

Changing the root app
---------------------

If you want to e.g. change the URL for the catalogue app from ``/catalogue``
to ``/catalog``, you need to use a custom root app instance
instead of Oscar's default instance.  Hence, create a subclass of Oscar's main
``Application`` class and override the ``get_urls`` method::

    # myproject/app.py
    from oscar import app

    class MyShop(app.Shop):
        # Override get_urls method
        def get_urls(self):
            urlpatterns = [
                url(r'^catalog/', include(self.catalogue_app.urls)),
                # all the remaining URLs, removed for simplicity
                # ...
            ]
            return urlpatterns

    application = MyShop()

As the root app is hardcoded in your project's ``urls.py``, you need to modify
it to use your new application instance instead of Oscar's default::

    # urls.py
    from myproject.app import application

    urlpatterns = [
       # Your other URLs
       url(r'', include(application.urls)),
    ]

All URLs containing ``catalogue`` previously are now displayed as ``catalog``.
