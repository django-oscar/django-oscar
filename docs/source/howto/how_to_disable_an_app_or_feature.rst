================================
How to disable an app or feature
================================

How to disable an app's URLs
============================

Suppose you don't want to use Oscar's dashboard but use your own.  The way to do
this is to modify the URLs config to exclude the URLs from the app in question.

You need to use your own root 'application' instance which gives you control
over the URLs structure.  So your root ``urls.py`` should have::

    # urls.py
    from myproject.app import application

    urlpatterns = [
        ...
        url(r'', include(application.urls)),
    ]

where ``application`` is a subclass of ``oscar.app.Shop`` which overrides the 
link to the dashboard app::

    # myproject/app.py
    from oscar.app import Shop
    from oscar.core.application import Application

    class MyShop(Shop):

        # Override the core dashboard_app instance to use a blank application 
        # instance.  This means no dashboard URLs are included.
        dashboard_app = Application()

The only remaining task is to ensure your templates don't reference any
dashboard URLs. 

How to disable Oscar feature
============================

You can add feature name to the setting ``OSCAR_HIDDEN_FEATURES`` and its application
URLs would be excluded from the URLconf. Template code, wrapped with the
``{% iffeature %}{% endiffeature %}`` block template tag, will not be rendered::

    {% iffeature "reviews" %}
        {% include "catalogue/reviews/partials/review_stars.html" %}
    {% endiffeature %}

Currently supported "reviews" and "wishlists" features. You can make your custom feature
hidable by setting ``hidable_feature_name`` property of the ``Application`` class::

    # myproject/apps/lottery/app.py
    from oscar.core.application import Application

    class LotterApplication(Application):
        hidable_feature_name = 'lottery'


Then, it needs to be added to the corresponding setting: ``OSCAR_HIDDEN_FEATURES = ['lottery']``.
Finally, you can wrap necessary template code with the ``{% iffeature "lottery" %}{% endiffeature %}``
tag as in the example above.