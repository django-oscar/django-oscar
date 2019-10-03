======================
Oscar design decisions
======================

The central aim of Oscar is to provide a solid core of an e-commerce project that can be
extended and customised to suit the domain at hand.  This is achieved in several ways:

Core models are abstract
------------------------

Online shops can vary wildly, selling everything from turnips to concert
tickets.  Trying to define a set of Django models capable for modelling all such
scenarios is impossible - customisation is what matters.

One way to model your domain is to have enormous models that have fields for
every possible variation; however, this is unwieldy and ugly.

Another is to use the Entity-Attribute-Value pattern to use add meta-data for each of
your models.  However this is again ugly and mixes meta-data and data in your database (it's
an SQL anti-pattern).

Oscar's approach to this problem is to have minimal but abstract models
where all the fields are meaningful within any e-commerce domain.  Oscar then
provides a mechanism for subclassing these models within your application so
domain-specific fields can be added.

Specifically, in many of Oscar's apps, there is an ``abstract_models.py`` module which
defines these abstract classes.  There is also an accompanying ``models.py`` which provides an
empty but concrete implementation of each abstract model.

Classes are loaded dynamically
------------------------------

The complexity of scenarios doesn't stop with Django models; core parts of
Oscar need to be as customisable as possible. Hence almost all classes
(including views) are
:doc:`dynamically loaded </topics/class_loading_explained>`,
which results in a maintainable approach to customising behaviour.

URLs and permissions for apps are handled by app config instances
-----------------------------------------------------------------

The :class:`oscar.core.application.OscarConfig` class handles mapping URLs
to views and permissions at an per-app level. This makes Oscar's apps more
modular, and makes it easy to customise this mapping as they can be overridden
just like any other class in Oscar.

Templates can be overridden
---------------------------

This is a common technique relying on the fact that the template loader can be
configured to look in your project first for templates, before it uses the defaults
from Oscar.
