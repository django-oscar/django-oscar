=======================
How to customise models
=======================

You must first create a local version of the app that you wish to customise.  This
involves creating a local app with the same name and importing the equivalent models
from oscar into it.

Example
-------

Suppose you want to add a video_url field to the core product model.  This means that
you want your application to use a subclass of ``oscar.apps.catalogue.models.Product`` which
has an additional field.

The first step is to create a local version of the "catalogue" app.  At a minimum, this 
involves creating ``catalogue/models.py`` within your project and changing ``INSTALLED_APPS``
to point to your local version rather than oscar's.  

Next, you can modify the ``Product`` model through subclassing::

    # yourproject/catalogue/models.py

    from django.db import models

    from oscar.apps.catalogue.abstract_models import AbstractProduct

    class Product(AbstractProduct):
        video_url = models.URLField()

Now, running ``./manage.py syncdb`` will create the product model with your additional field


