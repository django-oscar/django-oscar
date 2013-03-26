======================
Oscar Design Decisions
======================

The central aim of Oscar is to provide a solid core of an e-commerce project that can be
extended and customised to suit the domain at hand.  This is achieved in several ways:

Core models are abstract
------------------------

Online shops can vary wildly, selling everything from turnips to concert
tickets.  Trying to define a set of Django models capable for modeling all such
scenarios is impossible - customisation is what matters.

One way to model your domain is to have enormous models that have fields for
every possible variation; however, this is unwieldy and ugly.  

Another is to use the Entity-Attribute-Value pattern to use add meta-data for each of 
your models.  However this is again ugly and mixes meta-data and data in your database (it's 
an SQL anti-pattern).

Oscar's approach to this problem is to have have minimal but abstract models
where all the fields are meaningful within any e-commerce domain.  Oscar then
provides a mechanism for subclassing these models within your application so
domain-specific fields can be added.

Specifically, in many of Oscar's apps, there is an ``abstract_models.py`` module which
defines these abstract classes.  There is also an accompanying ``models.py`` which provides an
empty but concrete implementation of each abstract model.

Classes are loaded dynamically
------------------------------

To enable sub-apps to be overridden, Oscar classes are loading generically
using a special ``get_class`` function.  This looks at the
``INSTALLED_APPS`` tuple to determine the appropriate app to load a class from.

Sample usage::

    from oscar.core.loading import get_class

    Repository = get_class('shipping.repository', 'Repository')
    
This is a replacement for the usual::

    from oscar.apps.shipping.repository import Repository

It is effectively an extension of Django's ``django.db.models.get_model``
function to work with arbitrary classes.
    
The ``get_class`` function looks through your ``INSTALLED_APPS`` for a matching module to
the one specified and will load the classes from there.  If the matching module is
not from Oscar's core, then it will also fall back to the equivalent module if the
class cannot be found.

This structure enables a project to create a local ``shipping.repository`` module and 
subclass and extend the classes from ``oscar.app.shipping.repository``.  When Oscar
tries to load the ``Repository`` class, it will load the one from your local project.

All views are class-based
-------------------------

This enables any view to be subclassed and extended within your project.  

Templates can be overridden
---------------------------

This is a common technique relying on the fact that the template loader can be
configured to look in your project first for templates, before it uses the defaults
from Oscar.
