==================
Core functionality
==================

This page details the core classes and functions that Oscar uses.  These aren't
specific to one particular app, but are used throughout Oscar's codebase.

Dynamic class loading
---------------------

The key to Oscar's flexibility is dynamically loading classes.  This allows
projects to provide their own versions of classes that extend and override the
core functionality.

.. automodule:: oscar.core.loading
    :members: get_classes, get_class

URL patterns and views 
----------------------

Oscar's app organise their URLs and associated views using a "Application"
class instance.  This works in a similar way to Django's admin app, and allows
Oscar projects to subclass and customised URLs and views.

.. automodule:: oscar.core.application
    :members:

Prices
------

Oscar uses a custom price object for easier tax handling.  

.. automodule:: oscar.core.prices
    :members: Price

Custom model fields
-------------------

Oscar uses a few custom model fields.

.. automodule:: oscar.models.fields
    :members: 
