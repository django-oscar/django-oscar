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

Migrating apps
~~~~~~~~~~~~~~

Apps that you aren't customising will upgrade trivially as your project
will pick up the new migrations from Oscar directly.

For instance,  if you have ``oscar.apps.core.shipping`` in your
``INSTALLED_APPS`` then you can simply run::

    ./manage.py makemigrations shipping

to migrate your shipping app.

Migrating customised apps (models unchanged)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have customised an app, but have not touched the models nor migrations,
you're best off copying the migrations from Oscar.  This approach has the
advantage of pulling in any data migrations.
Find the updated(!) Oscar in your virtualenv or clone the Oscar repository at the
correct version tag. Then find the migrations, copy them across, and migrate as
usual.  You will have to adapt paths, but something akin to this will work::

    $ cdsitepackages oscar/apps/shipping/migrations
    $ copy *.py <your_project>/myshop/shipping/migrations/

.. _migrate_customised_apps_with_model_changes:

Migrating customised apps (models changed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At this point, you have essentially forked away from Oscar's migrations. You will
need to review all migrations that the Oscar release ships. Please also carefully
read the release notes; tricky migrations will usually be mentioned.

If there are data migrations, you will need to look into what they do, and
likely will have to imitate what they're doing. You can copy across the
`RunPython` part of data migration, but you have to mind the migration dependencies
to ensure your data migration is executed in the right order.

For schema migrations, it can sometimes be as easy as::

    ./manage.py makemigrations shipping

to mirror the changes Oscar did.

But other times, you will get dependency errors because new Oscar migrations
reference a migration you don't have. One can get around this by creating
an empty migration with the same name. See `this thread`_ on the mailing list.

Feel free to get in touch on the mailing list if you run into any problems.

.. _`this thread`: https://groups.google.com/g/django-oscar/c/2GL2XGHRcwM
