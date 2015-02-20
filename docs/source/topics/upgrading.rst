---------
Upgrading
---------

This document explains some of the issues that can be encountered whilst
upgrading Oscar.

Migrations
----------

Oscar provides migrations for its apps.  But since Oscar allows
an app to be overridden and its models extended, handling migrations can be
tricky when upgrading.  

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

Migrating customised apps (models unchanged)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have customised an app, but have not touched the models nor migrations,
you're best off copying the migrations from Oscar.  This approach has the
advantage of pulling in any data migrations.
Find the updated(!) Oscar in your virtualenv or clone the Oscar repo at the
correct version tag. Then find the migrations, copy them across, and migrate as
usual.  You will have to adapt paths, but something akin to this will work::

    $ cdsitepackages oscar/apps/shipping/migrations
    $ copy *.py <your_project>/myshop/shipping/migrations/

.. _migrate_customised_apps_with_model_changes:

Migrating customised apps (models changed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At this point, you have essentially forked away from Oscar's migrations. Read
the release notes carefully and see if it includes data migrations. If not,
it's as easy as::

    ./manage.py makemigrations shipping

to create the appropriate migration.

But if there is data migrations, you will need to look into what they do, and
likely will have to imitate what they're doing. You can copy across the
data migration, but you have to manually update the dependencies.

If there's no schema migrations, you should set the data migration to depend
on your last migration for that app. If there is a schema migration, you
will have to imitate the dependency order of Oscar.

Feel free to get in touch on the mailing list if you run into any problems.
