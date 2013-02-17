=====================================
How to change an existing URL pattern
=====================================

Oscar comes with a lot of different URLs set up for different parts of the
site. Some of these names might not be the right naming for your specific
project or you would like to switch the British spelling to the American one
as in ``catalogue`` to ``catalog``.

Taking this example, changing the URL from ``catalogue`` to ``catalog`` is
very simple. All you have to do is find the ``Application`` object that defines
the URL. In this case it's in ``oscar.app.py`` and contains the ``Shop`` class
that you are using in your projects ``urls.py`` to `register Oscar's URLs`_.

The ``Shop`` application defines its URLs in a method called ``get_urls`` and
all you have to do is change the patterns defined by this function. To do this,
just create a subclass of ``Shop`` and change the URL patterns to your hearts
contempt.


.. _`register Oscar's URLs`: http://django-oscar.readthedocs.org/en/latest/getting_started.html#urls


Changing a URL pattern
----------------------

Create a subclass of ``Shop``, copy the ``get_urls`` method and change the name
of the URL pattern::

    from oscar.app import Shop as CoreShop

    class MyShop(CoreShop):
        def get_urls(self):
        urlpatterns = patterns('',
            (r'^catalog/', include(self.catalogue_app.urls)),

            ... # all the remaining URLs, removed to simplify
        )
        return urlpatterns

All URLs containing ``catalogue`` previously are now displayed as ``catalog``.
