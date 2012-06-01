================
Design decisions
================

The central aim of oscar is to provide a solid core of an e-commerce project that can be
extended and customised to suit the domain at hand.  This is acheived in several ways:

Core models are abstract
------------------------

Online shops can vary wildly, selling everything from turnips to concert tickets.  Trying
to define a set of Django models capable for modelling all such scenarios is impossible -
customisation is what matters.

One way to model your domain is to have enormous models that have fields for
every possible variation; however, this is unwieldy and ugly.  

Another is to use the Entity-Attribute-Value pattern to use add meta-data for each of 
your models.  However this is again ugly and mixes meta-data and data in your database (it's 
an SQL anti-pattern).

Oscar's approach to this problem is to have have minimal but abstract models
where all the fields are meaningful within any e-commerce domain.  Oscar then
provides a mechanism for subclassing these models within your application so
domain-specific fields can be added.

Specifically, in each of oscar's apps, there is an ``abstract_models.py`` module which
defines these abstract classes.  There is also an accompanying ``models.py`` which provides an
empty but concrete implementation of each abstract model.

Classes are loaded dynamically
------------------------------

To enable sub-apps to be overridden, oscar classes are loading generically
using a special ``import_module`` function.  This looks at the
``INSTALLED_APPS`` tuple to determine the appropriate app to load a class from.

Within oscar itself, classes are imported using a special ``import_module`` function
which determines which app to load the specified classes from.  Sample usage is::

    import_module('product.models', ['Item', 'ItemClass'], locals())
    
This will load the ``Item`` and ``ItemClass`` classes into the local namespace.  It is
a replacement for the usual::

    from oscar.product.models import Item, ItemClass
    
The ``import_module`` looks through your ``INSTALLED_APPS`` for a matching module to
the one specified and will load the classes from there.  If the matching module is
not from oscar's core, then it will also fall back to the equivalent module if the
class cannot be found.

This structure enables a project to create a local ``product.models`` module and 
subclass and extend the core models from ``oscar.app.product.models``.  When Oscar
tries to load the ``Item`` class, it will load the one from your local project.

All views are class-based
-------------------------

This enables any view to be subclassed and extended within your project.  

Templates can be overridden
---------------------------

This is a common technique relying on the fact that the template loader can be
configured to look in your project first for templates, before it uses the defaults
from oscar.
