=================
Customising Oscar
=================

Many parts of Oscar can be adapted to your needs like any other Django
application:

* Many :doc:`settings</ref/settings>` control Oscar's behavior
* The looks can be controlled by extending or overriding the
  :doc:`templates </howto/how_to_customise_templates>`

But as Oscar is built as a highly customisable and extendable framework, it
doesn't stop there. The behaviour of all Oscar apps can heavily be altered
by injecting your own code.

To extend the behavior of an Oscar core app, some bootstrapping is required.
These steps are detailed below. After having completed this, you should
generally be able to override any class/model/view by just dropping it
in the right place and giving it the same name.

In some cases, customising is slightly more involved. The following how-tos
give plenty of examples for specific use cases:

* :doc:`/howto/how_to_customise_models`
* :doc:`/howto/how_to_change_a_url`
* :doc:`/howto/how_to_customise_a_view`

For a deeper understanding of customising Oscar, it is recommended to read
through the :doc:`/internals/design-decisions` and the concept of
:doc:`dynamic class loading</topics/class_loading_explained>`, as it underpins
most of what is detailed below.

Create Python module with same label
====================================

You need to create a Python module with the same "app label" as the Oscar app
you want to extend.
E.g., to create a local version of ``oscar.apps.order``, do the following::

    $ mkdir yourproject/order
    $ touch yourproject/order/__init__.py


Replace Oscar's app with your own in ``INSTALLED_APPS``
=======================================================

You will need to let Django know that you intend to replace one of Oscar's core
apps. You can do that by supplying an extra argument to
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


Reference Oscar's models
========================

If the original Oscar app has a ``models.py``, you'll need to create a
``models.py`` file in your local app. It should import all models from
the Oscar app being overridden::

    # yourproject/order/models.py

    # your custom models go here

    from oscar.apps.order.models import *

If two models with the same name are declared within an app, Django will only
use the first one. That means that if you wish to customise Oscar's models, you
must declare your custom ones before importing Oscar's models for that app.

If you're using South, you have to copy the ``migrations`` directory
from ``oscar/apps/order`` and put it into your ``order`` app. Detailed
instructions are available in :doc:`/howto/how_to_customise_models`.

Get the Django admin working
============================

When you replace one of Oscar's apps with a local one, Django admin integration
is lost. If you'd like to use it, you need to create an ``admin.py`` and import
the core app's ``admin.py`` (which will run the register code)::

    # yourproject/order/admin.py
    import oscar.apps.order.admin

This isn't great but we haven't found a better way as of yet.

Start customising!
==================

You can now override every class (that is
:doc:`dynamically loaded </topics/class_loading_explained>`, which is
almost every class) in the app you've replaced. That means forms,
views, strategies, etc. All you usually need to do is give it the same name
and place it in a module with the same name.

Suppose you want to alter the way order numbers are generated.  By default,
the class ``oscar.apps.order.utils.OrderNumberGenerator`` is used. So just
create a class within your ``order`` app which
matches the module path from oscar: ``order.utils.OrderNumberGenerator``.  This
could subclass the class from Oscar or not::

    # yourproject/order/utils.py

    from oscar.apps.order.utils import OrderNumberGenerator as CoreOrderNumberGenerator


    class OrderNumberGenerator(CoreOrderNumberGenerator):

        def order_number(self, basket=None):
            num = super(OrderNumberGenerator, self).order_number(basket)
            return "SHOP-%s" % num


