=======================
How to customise an app
=======================

A core part of how Oscar can be customised is to create a local version of one
of Oscar's apps so that it can be modified and extended.  Creating a local
version of an app allows customisation of any of the classes within the
corresponding app in oscar.

The way this is done involves a few steps, which are detailed here.

Method
======

1. Create an app within your project with the same "app label" as an app in oscar.  Eg,
   to create a local version of ``oscar.apps.order``, create something like ``myproject.order``.

2. Ensure the ``models.py`` in your local app imports all the models from Oscar's version::

    # models.py
    from oscar.apps.order.models import *

3. Replace Oscar's version of the app with your new version in ``INSTALLED_APPS``.


Worked example
==============

Suppose you want to modify the homepage view class, which by default is defined in
``oscar.apps.promotions.views.HomeView``.  This view is bound to a URL within the 
``PromotionsApplication`` class in ``oscar.apps.promotions.app`` - hence we need to 
override this application class to be able to use a different view.

By default, your base ``urls.py`` should include Oscar's URLs as so::

    # urls.py
    from oscar.app import application

    urlpatterns = patterns('',
        ...
        (r'', include(application.urls)),
    )

To get control over the mapping between URLs and views, you need to use a local
``application`` instance, that (optionally) subclasses Oscar's.  Hence, create 
``myproject/app.py`` with contents::

    # myproject/app.py
    from oscar.app import Shop

    class BaseApplication(Shop):
        pass

    application = BaseApplication()

No customisation for now, that will come later, but you now have control over which
URLs and view functions are used.  

Now hook this up in your ``urls.py``::

    # urls.py
    from myproject.app import application

    urlpatterns = patterns('',
        ...
        (r'', include(application.urls)),
    )

The next step is to create a local app with the same name as the app you want to override::

    mkdir myproject/promotions
    touch myproject/promotions/__init__.py
    touch myproject/promotions/models.py

The ``models.py`` file should import all models from the oscar app being overridden::

    # myproject/promotions/models.py
    from oscar.apps.promotions.models import *

Now replace ``oscar.apps.promotions`` with  in the ``INSTALLED_APPS``
setting in your settings file. To do it, you will need to let Oscar know that 
you're replacing the corresponding core app with yours.  
You can do that by supplying an extra argument to ``get_core_apps`` function::

    # myproject/settings.py

    from oscar import get_core_apps
    # ...
    INSTALLED_APPS = [
    ] + get_core_apps(['myproject.promotions'])

The ``get_core_apps`` function will replace ``oscar.apps.promotions`` with
``myproject.promotions``.

Now create a new homepage view class in ``myproject.promotions.views`` - you can subclass
Oscar's view if you like::

    from oscar.apps.promotions.views import HomeView as CoreHomeView

    class HomeView(CoreHomeView):
        template_name = 'promotions/new-homeview.html'

In this example, we set a new template location but it's possible to customise the view
in any imaginable way.

Now create a ``templates`` directory inside of ``myproject.promotions``. This should not be a 
python package but rather a plain directory without the ``__init__.py`` file. Inside of this 
directory create another directory called ``promotions``. Finally, inside of that directory
create a new HTML template called ``new-homeview.html``. For now, put something simple
in there, such as::

    <html>
    <body>
    <p>You have successfully overridden the homepage template.</p>
    </body>
    </html>

Next, create a new ``app.py`` for your local promotions app which maps your new ``HomeView``
class to the homepage URL::

    # myproject/promotions/app.py
    from oscar.apps.promotions.app import PromotionsApplication as CorePromotionsApplication

    from myproject.promotions.views import HomeView

    class PromotionsApplication(CorePromotionsApplication):
        home_view  = HomeView

    application = PromotionsApplication()

Finally, hook up the new view to the homepage URL::

    # myproject/app.py
    from oscar.app import Shop

    from myproject.promotions.app import application as promotions_app

    class BaseApplication(Shop):
        promotions_app = promotions_app

    application = BaseApplication()

Quite long-winded, but once this step is done, you have lots of freedom to customise
the app in question.

Django admin
------------

One pain point with replacing one of Oscar's apps with a local one in
``INSTALLED_APPS`` is that admin integration is lost from the original 
app. If you'd like to use the Django admin functionality you just need 
to run the register code in the replaced app's ``admin.py``::

    # myprojects/promotions/admin.py
    import oscar.apps.promotions.admin

This isn't great but we haven't found a better way as of yet.
