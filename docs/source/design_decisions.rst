================
Design decisions
================

Oscar's is designed to be open to customisation wherever possible.  There are two
main ways in which this is acheived.

Dynamic importing of classes
----------------------------

Within oscar itself, classes are imported using a special ``import_module`` function
which determines which app to load the specified classes from.  Sample usage is::

    import_module('product.models', ['Item', 'ItemClass'], locals())
    
This will load the ``Item`` and ``ItemClass` classes into the local namespace.  It is
a replacement for the usual::

    from oscar.product.models import Item, ItemClass
    
The ``import_module`` looks through your ``INSTALLED_APPS`` for a matching module to
the one specified and will load the classes from there.  If the matching module is
not from oscar's core, then it will also fall back to the equivalent module if the
class cannot be found.

This structure enables a project to create a local ``product.models`` module and 
subclass and extend the core models from ``oscar.app.product.models``.  When Oscar
tries to load the ``Item`` class, it will load the one from your local project.

Class-based views
-----------------

All views within oscar's core are class-based, which allows the above dynamic class
loading to be used within ``urls.py`` modules, so that core views can be subclassed
within projects to extend and customised them.

