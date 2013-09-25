==============================
How to use a custom user model
==============================

If you are using Django 1.5 or later, then you can specify a custom user model
in your settings.  Oscar will dynamically adjust the profile summary view and
profile editing form to use the fields from your custom model.  

Before Django 1.5, the recommended technique for adding fields to users was to
use a one-to-one "profile" model specified in the ``AUTH_PROFILE_MODULE``.  As
of Django 1.5, this setting is deprecated and will be removed_ in Django 1.7.
Nevertheless, Oscar continues to support this setting and will add relevant
fields to the profile form.  Hence profiles can be used in combination with
custom user models.  That doesn't mean it's a good idea.

.. _removed: https://docs.djangoproject.com/en/1.5/internals/deprecation/#id4

Restrictions
------------

Oscar does have some requirements on what fields a user model has.  For
instance, the auth backend requires a user to have an 'email' and 'password'
field.  

Oscar 0.6 ships with its own abstract user model that supports the minimum
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
table in a manual schemamigration.
