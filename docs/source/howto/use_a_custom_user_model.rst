==============================
How to use a custom user model
==============================

You can specify a custom user model in the ``AUTH_USER_MODEL`` setting.
Oscar will dynamically adjust the account profile summary view and
profile editing form to use the fields from your custom model.

Before Django 1.5, the recommended technique for adding fields to users was to
use a one-to-one "profile" model specified in the ``AUTH_PROFILE_MODULE``.
While this setting was removed from Django in Django 1.7, Oscar continues to
support it and will add relevant fields to the profile form.
Hence profiles can be used in combination with custom user models.
That doesn't mean it's a good idea.

Restrictions
------------

Oscar does have some requirements on what fields a user model has.  For
instance, the authentication backend requires a user to have an 'email' and
'password' field. Oscar also assumes that the ``email`` field is unique, as
this is used to identify users.

Oscar ships with its own abstract user model that supports the minimum
fields and methods required for Oscar to work correctly.  New Oscar projects
are encouraged to subclass this User model.

Migrations
----------

It has previously been suggested to set ``db_table`` of the model to
``auth_user`` to avoid the migrations from breaking. This issue has been fixed
and migrations are now using ``AUTH_USER_MODEL`` and ``AUTH_USER_MODEL_NAME``
which will use ``db_table`` name of the user model provided by
``get_user_model()``.

This works in the instances where you are using the default ``auth.User`` model
or when you use a custom user model from the start. Switching over from
``auth.User`` to a custom model after having applied previous migration of
Oscar will most likely require renaming the ``auth_user`` table to the new user
table in a manual migration.

Example
-------

If you want to use ``oscar.apps.customer.abstract_model.AbstractUser``
which has ``email`` as an index, and want to customise some of the methods on
``User`` model, say, ``get_full_name`` for Asian names, a simple approach is
to create your own ``user`` module::

    # file: your-project/apps/user/models.py
    from django.db import models

    from oscar.apps.customer.abstract_models import AbstractUser


    class User(AbstractUser):

        def get_full_name(self):
            full_name = '%s %s' % (self.last_name.upper(), self.first_name)
            return full_name.strip()

Then add this ``user`` app to the ``INSTALLED_APPS`` list. Beside that we
need to tell ``django`` to use our customised user model instead of the
default one as the authentication model [1]_::

    # use our own user model
    AUTH_USER_MODEL = "user.User"

After the migration, a database table called ``user_user`` will be created based
on the schema defined inside of
``oscar.apps.customer.abstract_models.AbstractUser``.


  .. [1] https://docs.djangoproject.com/en/stable/ref/settings/#auth-user-model
