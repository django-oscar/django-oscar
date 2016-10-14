=======================
How to customise models
=======================

This How-to describes how to replace Oscar models with your own. This allows you
to add fields and custom methods.  It builds upon the steps described in
:doc:`/topics/customisation`. Please read it first and ensure that you've:

* Created a Python module with the the same app label
* Added it as Django app to ``INSTALLED_APPS``
* Added a ``models.py`` and ``admin.py``

Example
-------

Suppose you want to add a ``video_url`` field to the core product model.  This means
that you want your application to use a subclass of
:class:`oscar.apps.catalogue.abstract_models.AbstractProduct` which has an additional field.

The first step is to create a local version of the "catalogue" app.  At a minimum, this 
involves creating ``catalogue/models.py`` within your project and changing ``INSTALLED_APPS``
to point to your local version rather than Oscar's.  

Next, you can modify the ``Product`` model through subclassing::

    # yourproject/catalogue/models.py

    from django.db import models

    from oscar.apps.catalogue.abstract_models import AbstractProduct

    class Product(AbstractProduct):
        video_url = models.URLField()

    from oscar.apps.catalogue.models import *

Make sure to import the remaining Oscar models at the bottom of your file. 

.. tip::

   Using ``from ... import *`` is strange isn't it?  Yes it is, but it needs to
   be done at the bottom of the module due to the way Django registers models.
   The order that model classes are imported makes a difference, with only the
   first one for a given class name being registered.

The last thing you need to do now is make Django update the database schema and
create a new column in the product table. We recommend using migrations 
for this (internally Oscar already does this) so all you need to do is create a
new schema migration. 

It is possible to simply create a new catalogue migration (using ``./manage.py
makemigrations catalogue``) but this isn't recommended as any
dependencies between migrations will need to be applied manually (by adding a
``dependencies`` attribute to the migration class).

The recommended way to handle migrations is to copy the ``migrations`` directory
from ``oscar/apps/catalogue`` into your new ``catalogue`` app.  Then you can
create a new (additional) migration using the ``makemigrations``
management command::

    ./manage.py makemigrations catalogue

which will pick up any customisations to the product model.

To apply the migration you just created, all you have to do is run
``./manage.py migrate catalogue`` and the new column is added to the product
table in the database.

Customising Products
--------------------

You should inherit from ``AbstractProduct`` as above to alter behaviour for all
your products. Further subclassing is not recommended, because using methods
and attributes of concrete subclasses of ``Product`` are not available unless
explicitly casted to that class.
To model different classes of products, use ``ProductClass`` and
``ProductAttribute`` instead.

Model customisations are not picked up
--------------------------------------

It's a common problem that you're trying to customise one of Oscar's models,
but your new fields don't seem to get picked up. That is usually caused by
Oscar's models being imported before your customised ones. Django's model 
registration disregards all further model declarations.

In your overriding ``models.py``, ensure that you import Oscar's models *after*
your custom ones have been defined. If that doesn't help, you have an import 
from ``oscar.apps.*.models`` somewhere that is being executed before your models 
are parsed. One trick for finding that import: put ``assert False`` in the relevant 
Oscar's models.py, and the stack trace will show you the importing module.

If other modules need to import your models, then import from your local module,
not from Oscar directly.
