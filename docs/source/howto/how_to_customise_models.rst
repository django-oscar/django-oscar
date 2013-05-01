=======================
How to customise models
=======================

This How-to describes how to replace Oscar models with your own. This allows you
to add fields and custom methods.
It builds upon the steps described in :doc:`/topics/customisation`. Please
read it first and ensure that you've:

* Created a Python module with the the same label
* Added it as Django app

Example
-------

Suppose you want to add a video_url field to the core product model.  This means
that you want your application to use a subclass of
:class:`oscar.apps.catalogue.models.Product` which has an additional field.

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

The last thing you need to do now is make Django update the database schema and
create a new column in the product table. We recommend to use South migrations 
for this (internally Oscar already uses it) so all you need to do is create a
new schema migration. Depending on your setup you should follow one of these
two options:

1. You **have not** run ``./manage.py migrate`` before

   You can simply generate a new initial migration using::

    ./manage.py schemamigration catalogue --initial

2. You **have** run ``./manage.py migrate`` before

   You have to copy the ``migrations`` directory from ``oscar/apps/catalogue``
   (the same as the ``models.py`` you just copied) and put it into your
   ``catalogue`` app.
   Now create a new (additional) schemamigration using the ``schemamigration``
   management command and follow the instructions::

    ./manage.py schemamigration catalogue --auto

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
