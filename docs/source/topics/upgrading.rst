---------
Upgrading
---------

This document explains some of the issues that can be encountered whilst
upgrading Oscar.

.. note::

    Detailed upgrade instructions for specific releases can be found on the `Github
    wiki`_.

.. _`Github wiki`: https://github.com/tangentlabs/django-oscar/wiki/Upgrading

Migrations
----------

Oscar uses South_ to provide migrations for its apps.  But since Oscar allows
an app to be overridden and its models extended, handling migrations can be
tricky when upgrading.  

.. _South: http://south.readthedocs.org/en/latest/installation.html

Suppose a new version of Oscar changes the models of the 'shipping' app and
includes the corresponding migrations.  There are two scenarios to be aware of:

Migrating uncustomised apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apps that you aren't customising will upgrade trivially as your project
will pick up the new migrations from Oscar directly.  

For instance,  if you have ``oscar.apps.core.shipping`` in your
``INSTALLED_APPS`` then you can simply run::

    ./manage.py migrate shipping

to migrate your shipping app.

Migrating customised apps
~~~~~~~~~~~~~~~~~~~~~~~~~

For apps that you are customising, you need to create a new migration that picks
up the changes in the core Oscar models.
For instance,  if you have an app ``myproject.shipping`` that replaces
``oscar.apps.shipping`` in your ``INSTALLED_APPS`` then you can simply run::

    ./manage.py schemamigration shipping --auto

to create the appropriate migration.
