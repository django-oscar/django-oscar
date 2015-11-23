==============
Forking an app
==============

This guide explains how to fork an app in Oscar.

.. note::

  The following steps are now automated by the ``oscar_fork_app`` management
  command. They're explained in detail so you get an idea of what's going on.
  But there's no need to do this manually anymore! More information is available in :doc:`/topics/customisation#fork-the-oscar-app`.

Create Python module with same label
====================================

You need to create a Python module with the same "app label" as the Oscar app
you want to extend. E.g., to create a local version of ``oscar.apps.order``,
do the following::

    $ mkdir yourproject/order
    $ touch yourproject/order/__init__.py

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

You have to copy the ``migrations`` directory from ``oscar/apps/order`` and put
it into your ``order`` app. Detailed instructions are available in
:doc:`/howto/how_to_customise_models`.

Get the Django admin working
============================

When you replace one of Oscar's apps with a local one, Django admin integration
is lost. If you'd like to use it, you need to create an ``admin.py`` and import
the core app's ``admin.py`` (which will run the register code)::

    # yourproject/order/admin.py
    import oscar.apps.order.admin

This isn't great but we haven't found a better way as of yet.

Django 1.7+: Use supplied app config
====================================

Oscar ships with an app config for each app, which sets app labels and
runs startup code. You need to make sure that happens.

.. code-block: django

    # yourproject/order/config.py

    from oscar.apps.order import config


    class OrderConfig(config.OrderConfig):
        name = 'yourproject.order'

    # yourproject/order/__init__.py

    default_app_config = 'yourproject.order.config.OrderConfig'
