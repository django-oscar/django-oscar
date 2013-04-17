=====================================
How to change an existing URL pattern
=====================================

Oscar has many views and associated URLs.  Often you want to customise these
URLs for your domain.  For instance, you might want to use American spellings
rather than British (``catalog`` instead of ``catalogue``).

This How-to describes how to do just that.
It builds upon the steps described in :doc:`/topics/customisation`. Please
read it first and ensure that you've:

* Created an app with the same label
* Overridden the Oscar app with your own
* Created a custom ``app.py``

Example
-------

In order to customise Oscar's URLs, you need to use a custom app instance in
your root ``urls.py`` instead of Oscar's default instance.  Hence, to use
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
