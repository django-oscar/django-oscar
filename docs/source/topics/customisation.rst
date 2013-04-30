=================
Customising Oscar
=================

Many parts of Oscar can be adapted to your needs like any other Django
application.

* Many :doc:`settings</ref/settings>` control Oscar's behavior
* The looks can be controlled by extending or overriding the
  :doc:`templates </howto/how_to_customise_templates>`

But as Oscar is built as a highly customisable and extendable framework, it
doesn't stop there. Almost every aspect of it can be altered.
:doc:`Various techniques </internals/design-decisions>` are employed to achieve
that level of adaptability.

To extend the behavior of a Oscar core app, you will at least need to create an
app with the same label. Depending on what should be adapted, different steps
are necessary beyond that. The steps are detailed below; this overview might
help you to figure out what needs to be done.

==================================  ====================  ====================================  ========================
Goals vs. necessary steps           Override model class  Override view class (or change URLs)  Override any other class
==================================  ====================  ====================================  ========================
Create app with same label          Necessary             Necessary                             Necessary
Custom Shop class                   Not necessary         Necessary                             Not necessary
Custom Application class            Not necessary         Necessary                             Not necessary
Override app in ``INSTALLED_APPS``  Necessary             Not necessary                         Necessary
==================================  ====================  ====================================  ========================

If more complex changes are desired, it is usually easiest to do all of the
steps.
Please also refer to the following how-tos for further instructions and examples.

* :doc:`/howto/how_to_customise_models`
* :doc:`/howto/how_to_change_a_url`
* :doc:`/howto/how_to_customise_a_view`
* :doc:`/howto/how_to_override_a_core_class`

Create app with same label
==========================

All advanced customisation requires creating an a Python package with the same
"app label" as the Oscar app you want to extend.
E.g., to create a local version of ``oscar.apps.order``, do the following::

    $ mkdir yourproject/order
    $ touch yourproject/order/__init__.py


Custom Shop class
=================

Oscar's views and URLs use a tree of 'app' instances, each of which subclass
``oscar.core.application.Application`` and provide ``urls`` property.  Oscar has
a root app instance in ``oscar/app.py`` which can be imported into your
``urls.py``::

    # urls.py
    from oscar.app import application

    urlpatterns = patterns('',
       ... # Your other URLs
       (r'', include(application.urls)),
    )

To get control over the mapping between URLs and views, you need to use a local
``application`` instance, that (usually) subclasses Oscar's.  Hence, create
``yourproject/app.py`` with contents::

    # yourproject/app.py
    from oscar.app import Shop

    class BaseApplication(Shop):
        pass

    application = BaseApplication()


Now hook this up in your ``urls.py``::

    # urls.py
    from yourproject.app import application

    urlpatterns = patterns('',
        ...
        (r'', include(application.urls)),
    )

This step only needs to be done once. All customisation will only entail
overriding parts of the newly created ``BaseApplication``.

Custom application class
========================

If you want to modify a view or change a URL, you need to create an ``app.py``
for your local app. It will usually inherit from Oscar's version::

    # yourproject/order/app.py

    from oscar.apps.promotions.app import PromotionsApplication as CorePromotionsApplication

    class PromotionsApplication(CorePromotionsApplication):
        pass

    application = PromotionsApplication()

and hook it up in your main ``app.py``::

    # yourproject/app.py
    from oscar.app import Shop

    from yourproject.promotions.app import application as promotions_app

    class BaseApplication(Shop):
        promotions_app = promotions_app


Override app in INSTALLED_APPS
==============================

You will need to add your app ``INSTALLED_APPS`` to override Oscar's version
of the app with yours.  You can do that by supplying an extra argument to
``get_core_apps`` function::

    # settings.py

    from oscar import get_core_apps
    # ...
    INSTALLED_APPS = [
        # all your non-Oscar apps
    ] + get_core_apps(['yourproject.order'])

``get_core_apps([])`` will return a list of Oscar core apps. If you supply a
list of additional apps, they will be used to replace the Oscar core apps.
In the above example, ``yourproject.order`` will be returned instead of
``oscar.apps.order``.

To get your app working, you might also need to create a custom ``models.py``
and ``admin.py``.

models.py
---------

If the original Oscar app has a ``models.py``, you'll need to create a
``models.py`` file in your local app. It should import all models from
the oscar app being overridden::

    # yourproject/order/models.py

    # your custom models go here

    from oscar.apps.order.models import *

If two models with the same name are declared within an app, Django will only
use the first one. That means that if you wish to customise Oscar's models, you
must declare your custom ones before importing Oscar's models for that app.

admin.py
--------

When you replace one of Oscar's apps with a local one, Django admin integration
is lost. If you'd like to use it, you need to create an ``admin.py`` and import
the core app's ``admin.py`` (which will run the register code)::

    # yourproject/order/admin.py
    import oscar.apps.order.admin

This isn't great but we haven't found a better way as of yet.
