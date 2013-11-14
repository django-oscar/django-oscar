=====================================
How to change an existing URL pattern
=====================================

Oscar has many views and associated URLs.  Often you want to customise these
URLs for your domain.  For instance, you might want to use American spellings
rather than British (``catalog`` instead of ``catalogue``).

This How-to describes how to do just that.
It builds upon the steps described in :doc:`/topics/customisation`. Please
read it first and ensure that you've:

* Created a Python module with the the same label
* Added it as Django app to ``INSTALLED_APPS``
* Created a custom ``app.py``

Example
-------

In order to customise Oscar's URLs, you need to use a custom app instance
instead of Oscar's default instance.  ``/catalogue`` is wired up in the root
application, so we need to replace that. Hence, to use
``catalog`` instead of ``catalogue``, create a subclass of Oscar's main
``Application`` class and override the ``get_urls`` method::

    # myproject/app.py
    from oscar import app

    class MyShop(app.Shop):

        # Override get_urls method
        def get_urls(self):
            urlpatterns = patterns('',
                (r'^catalog/', include(self.catalogue_app.urls)),

                ... # all the remaining URLs, removed for simplicity
            )
            return urlpatterns

    application = MyShop()

Now modify your root ``urls.py`` to use your new application instance::

    # urls.py
    from myproject.app import application

    urlpatterns = patterns('',
       ... # Your other URLs
       (r'', include(application.urls)),
    )

All URLs containing ``catalogue`` previously are now displayed as ``catalog``.

If you wanted to change URLs of a sub-app (e.g. ``/catalogue/category/``),
you only need to replace the ``catalogue`` app. There's no need to change
your ``urls.py`` or touch the root ``application`` instance. ``application``
instances dynamically load their sub-apps, so it just pick up your replacement::

    # oscar/app.py
    class Shop(Application):
        name = None

        catalogue_app = get_class('catalogue.app', 'application')
        customer_app = get_class('customer.app', 'application')
        ...
