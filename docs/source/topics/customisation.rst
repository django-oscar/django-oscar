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

To extend the behavior of an Oscar core app, you will at least need to create an
app with the same label. Depending on what should be adapted, different steps
are necessary beyond that. The steps are detailed below; this overview might
help you to figure out what needs to be done.

================================  =============================  =================  =================
Goals vs. necessary steps         Python module with same label  Add as Django app  Custom ``app.py``
================================  =============================  =================  =================
Override a model class            Necessary                      Necessary          Not necessary
Override any other class or view  Necessary                      Necessary          Not necessary
Change app URLs or add views      Necessary                      Necessary          Necessary
================================  =============================  =================  =================

Please also refer to the following how-tos for further instructions and examples.

* :doc:`/howto/how_to_customise_models`
* :doc:`/howto/how_to_change_a_url`
* :doc:`/howto/how_to_customise_a_view`
* :doc:`/howto/how_to_override_a_core_class`

Python module with same label
=============================

All advanced customisation requires creating an a Python module with the same
"app label" as the Oscar app you want to extend.
E.g., to create a local version of ``oscar.apps.order``, do the following::

    $ mkdir yourproject/order
    $ touch yourproject/order/__init__.py


Custom ``app.py``
=================

Oscar's views and URLs use a tree of 'app' instances, each of which subclass
:class:`oscar.core.application.Application` and provide ``urls`` property.
Oscar has a root app instance in ``oscar/app.py`` which should already be
wired up in your ``urls.py``::

    # urls.py
    from oscar.app import application

    urlpatterns = patterns('',
       ... # Your other URLs
       (r'', include(application.urls)),
    )

Modifying root app
------------------

If you want to change URLs or views of the root application above, you need to
replace it with your own ``application`` instance, that (usually) subclasses
Oscar's.  Hence, create ``yourproject/app.py`` with contents::

    # yourproject/app.py
    from oscar.app import Shop

    class BaseApplication(Shop):
        pass

    application = BaseApplication()


Now hook this up in your ``urls.py`` instead::

    # urls.py
    from yourproject.app import application

    urlpatterns = patterns('',
        ...
        (r'', include(application.urls)),
    )

Modifying sub-apps
------------------

Sub-apps such as the ``catalogue`` app are loaded dynamically, just as most
other classes in Oscar::

    # oscar/app.py
    class Shop(Application):
        name = None

        catalogue_app = get_class('catalogue.app', 'application')
        customer_app = get_class('customer.app', 'application')
        ...

That means you can leave the root app unchanged, and just need to create another
``application`` instance. It will usually inherit from Oscar's version::

    # yourproject/promotions/app.py

    from oscar.apps.promotions.app import PromotionsApplication as CorePromotionsApplication
    from .views import MyExtraView

    class PromotionsApplication(CorePromotionsApplication):
        extra_view = MyExtraView

    application = PromotionsApplication()


Add as Django app
=================

You will need to let Django know that you intend to replace one of Oscar's core
apps. This means overriding it in ``INSTALLED_APPS`` and creating a few hooks
back to the replaced Oscar app.

``INSTALLED_APPS`` override
---------------------------

You will need to replace Oscar's version of the app with yours in
``INSTALLED_APPS`` .  You can do that by supplying an extra argument to
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

If you're using South, you probably have to copy the ``migrations`` directory
from ``oscar/apps/order`` and put it into your ``order`` app. Detailed
instructions are available in :doc:`/howto/how_to_customise_models`.

admin.py
--------

When you replace one of Oscar's apps with a local one, Django admin integration
is lost. If you'd like to use it, you need to create an ``admin.py`` and import
the core app's ``admin.py`` (which will run the register code)::

    # yourproject/order/admin.py
    import oscar.apps.order.admin

This isn't great but we haven't found a better way as of yet.
