==============================
How to use a custom user model
==============================

If you are using Django 1.5 or later, then you can specify a custom user model
in your settings.  Oscar will dynamically adjust the profile summary view and
profile editing form to use the fields from your custom model.  

Before Django 1.5, the recommended technique for adding fields to users was to
use a one-to-one "profile" model specified in the ``AUTH_PROFILE_MODULE``.
Oscar continues to support this setting and will add relevant fields to the
profile form.  Hence profiles can be used in combination with custom user
models.

Restrictions
------------

Oscar does have some requirements on what fields a user model has.  For
instance, the auth backend requires a user to have an 'email' and 'password'
field.  

Oscar 0.6 ships with its own abstract user model that supports the minimum
fields and methods required for Oscar to work correctly.  New Oscar projects are
encouraged to subclass this User model.
