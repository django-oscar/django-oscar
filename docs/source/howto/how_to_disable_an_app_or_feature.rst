================================
How to disable an app or feature
================================

How to disable an app's URLs
============================

Suppose you don't want to use Oscar's dashboard but use your own.  The way to do
this is to modify the URLs config to exclude the URLs from the app in question.

You need to use your own root app config, which gives you control over the URLs
structure.  So your root ``urls.py`` should have::

    # urls.py
    from django.apps import apps

    urlpatterns = [
        ...
        path('', include(apps.get_app_config('myproject').urls[0])),
    ]

where ``myproject`` is a Django/Oscar app with an app config class that is a
subclass of ``oscar.config.Shop`` which excludes the URL configuration for
the dashboard app::

    # myproject/config.py
    from oscar.config import Shop
    from oscar.core.application import OscarConfig

    class MyShop(Shop):

        # Override the get_urls method to remove the URL configuration for the
        # dashboard app
        def get_urls(self):
            urls = super().get_urls()
            for urlpattern in urls[:]:
                if hasattr(urlpattern, 'app_name') and (urlpattern.app_name == 'dashboard'):
                    urls.remove(urlpattern)
            return self.post_process_urls(urls)

    # myproject/__init__.py
    default_app_config = 'myproject.config.MyShop'

The only remaining task is to ensure your templates don't reference any
dashboard URLs.

How to disable Oscar feature
============================

You can add feature name to the setting ``OSCAR_HIDDEN_FEATURES`` and its app
config URLs would be excluded from the URLconf. Template code, wrapped with the
``{% iffeature %}{% endiffeature %}`` block template tag, will not be rendered::

    {% iffeature "reviews" %}
        {% include "catalogue/reviews/partials/review_stars.html" %}
    {% endiffeature %}

Currently supported "reviews" and "wishlists" features. You can make your custom feature
hidable by setting ``hidable_feature_name`` property of the ``OscarConfig`` class::

    # myproject/apps/lottery/apps.py
    from oscar.core.application import OscarConfig

    class LotterConfig(OscarConfig):
        hidable_feature_name = 'lottery'


Then, it needs to be added to the corresponding setting: ``OSCAR_HIDDEN_FEATURES = ['lottery']``.
Finally, you can wrap necessary template code with the ``{% iffeature "lottery" %}{% endiffeature %}``
tag as in the example above.
