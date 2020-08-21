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

The app config class
--------------------

Each Oscar app comes with an app config class which inherits from
:class:`oscar.core.application.OscarConfig` or
:class:`oscar.core.application.OscarDashboardConfig`. They're mainly used to
gather URLs (with the correct permissions) for each Oscar app. This structure
makes Oscar apps more modular as each app is responsible for its own URLs. And
as it is a class, it can be overridden like any other Oscar class; hence making
it straightforward to change URLs or add new views.
Each app config instance exposes a ``urls`` property, which is used to access
the list of URLs of an app, together with their application and instance
namespace.

The app config tree
-------------------

Oscar's app config instances are organised in a tree structure. The root app
config class illustrates this nicely::

    # oscar/config.py
    from django.apps import apps
    from oscar.core.application import OscarConfig

    class Shop(OscarConfig):
        name = 'oscar'

        def ready(self):
            self.catalogue_app = apps.get_app_config('catalogue')
            self.basket_app = apps.get_app_config('basket')
            # ...

        def get_urls(self):
            urls = [
                path('catalogue/', self.catalogue_app.urls),
                path('basket/', self.basket_app.urls),
                # ...
            ]

The root app config pulls in the URLs from its children. That means to add
all Oscar URLs to your Django project, you only need to include the list of URLs
(the first element of the ``urls`` property's value) from the root app config::

    # urls.py
    from django.apps import apps

    urlpatterns = [
        # Your other URLs
        path('', include(apps.get_app_config('oscar').urls[0])),
    ]

Changing sub apps
-----------------

:py:class:`~django.apps.config.AppConfig` of sub apps such as the ``catalogue`` app are dynamically
obtained by looking them up in the Django app registry::

    # oscar/config.py
    from django.apps import apps
    from oscar.core.application import OscarConfig

    class Shop(OscarConfig):
        name = 'oscar'

        def ready(self):
            self.catalogue_app = apps.get_app_config('catalogue')
            self.customer_app = apps.get_app_config('customer')
            # ...

That means you just need to create another app config class. It will usually
inherit from Oscar's version. Say you'd want to add another view to the
``offer`` app. You only need to create a class called ``OfferConfig``
(and usually inherit from Oscar's version) and add your view and its URL
configuration::

    # yourproject/offer/apps.py

    from oscar.apps.offer.apps import OfferConfig as CoreOfferConfig
    from .views import MyExtraView

    class OfferConfig(CoreOfferConfig):
        def ready(self):
            super().ready()
            self.extra_view = MyExtraView

        def get_urls(self):
            urls = super().get_urls()
            urls += [
                path('extra/', self.extra_view.as_view(), name='extra'),
            ]
            return self.post_process_urls(urls)

Changing the root app
---------------------

If you want to e.g. change the URL for the ``catalogue`` app from ``/catalogue``
to ``/catalog``, you need to use a custom root app config class,  instead of
Oscar's default class. Hence, create a subclass of Oscar's main ``OscarConfig``
class and override the ``get_urls`` method::

    # myproject/apps.py
    from oscar import config

    class MyShop(config.Shop):
        # Override get_urls method
        def get_urls(self):
            urlpatterns = [
                path('catalog/', self.catalogue_app.urls),
                # all the remaining URLs, removed for simplicity
                # ...
            ]
            return urlpatterns

    # myproject/__init__.py
    default_app_config = 'myproject.apps.MyShop'

Then change ``urls.py`` to use your new :py:class:`~django.apps.config.AppConfig`
instead of Oscar's default::

    # urls.py
    from django.apps import apps

    urlpatterns = [
       # Your other URLs
       path('', include(apps.get_app_config('myproject').urls[0])),
    ]

All URLs containing ``/catalogue/`` previously are now displayed as ``/catalog/``.
