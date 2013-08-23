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
fields and methods required for Oscar to work correctly.  New Oscar projects are
encouraged to subclass this User model.

Migrations
----------

When using a custom User model, the table name for that model will likely
change. This breaks Oscar's migrations, throwing an error::

    Running migrations for analytics:
     - Migrating forwards to 0001_initial.
     > customer:0001_initial
    FATAL ERROR - The following SQL query failed: ALTER TABLE "customer_email" ADD CONSTRAINT "user_id_refs_id_2c2b8797" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
    The error was: relation "auth_user" does not exist

    Error in migration: customer:0001_initial
    DatabaseError: relation "auth_user" does not exist

The recommended solution is to enforce the table name to be identical to the
stock User model's one::

    # Custom User model
    class User(AbstractBaseUser, PermissionsMixin):

        [...]

        class Meta:
            db_table = 'auth_user'

