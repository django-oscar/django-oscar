=======================
How to customise models
=======================

You must first create a local version of the app that you wish to customise.  This
involves creating a local app with the same name and importing the equivalent models
from Oscar into it.

Example
-------

Suppose you want to add a video_url field to the core product model.  This means that
you want your application to use a subclass of ``oscar.apps.catalogue.models.Product`` which
has an additional field.

The first step is to create a local version of the "catalogue" app.  At a minimum, this 
involves creating ``catalogue/models.py`` within your project and changing ``INSTALLED_APPS``
to point to your local version rather than Oscar's.  

Next, you can modify the ``Product`` model through subclassing::

    # yourproject/catalogue/models.py

    from django.db import models

    from oscar.apps.catalogue.abstract_models import AbstractProduct

    class Product(AbstractProduct):
        video_url = models.URLField()


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
