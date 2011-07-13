Introduction
============

Named after Oscar Peterson (http://en.wikipedia.org/wiki/Oscar_Peterson),
django-oscar is a flexible ecommerce platform, designed to build domain-driven
ecommerce sites.  It is not supposed to be a framework that can
be downloaded and fully set up by simply adjusting a configuration file: there
will always be some developer work required to make sure the models match those
from your domain - this is the nature of domain modelling.

That said, a small amount of work up front in determine the right models for your
shop can really pay off in terms of building a high-quality application that
is a pleasure to work with and maintain.  It's better to extend core models with fields
relevant to your domain that attempting to write code so "generic" that is can handle
any situation.  This generally leads to a confusing mess.

Aims of project
---------------

*   To be a portable Django application that provides ecommerce functionality.  
*   To comprise a set of loosely coupled apps that can be overridden in;
    projects (interdependence is on interfaces only);
*   To be highly customisable so any part of the core can be customised.

The central aim is to provide a solid core of an ecommerce project that can be
extended and customised to suit the domain at hand.  One way to acheive this is
to have enormous models that have fields for every possible variation; however,
this is unwieldy and ugly.  

A more elegant solution is to have minimal models where all the fields are meaningful
within any ecommerce domain.  In general, this means more work up front in
terms of creating the right set of models but leads ultimately to a much
cleaner and coherent system.

Core design decisions
---------------------

The central aim of django-oscar is to be a flexible app, that can be customised (rather than 
configured) to suit the domain at hand.  This is acheived in several ways:

*   **All core models are abstract.**  In each sub-app, there is an
    `abstract_models.py` file which
    defines abstract super-classes for every core model.  There is also an
    accompanying `models.py` file which provides a vanilla concrete implementation
    of each model.  The apps are structured this way so that any model can be
    subclassed and extended.  You would do this by creating an app in your project
    with the same top-level app label as the one you want to modify (eg
    `myshop.product` to modify `oscar.product`).  You can then create a models.py
    file which imports from the corresponding abstract models file but your
    concrete implementations can add new fields and methods.  For example, in a
    clothes shop, you might want your core `catalogue.Product` model to support fields
    for `Label`.  

*   **Avoidance of the [Entity-Attribute-Value](http://en.wikipedia.org/wiki/Entity-attribute-value_model) pattern**. 
    This technique of subclassing and extending models avoids an over-reliance
    on the using the EAV pattern which is commonly used to store data and
    meta-data about domain objects.  

*   **Classes are loaded generically.**  To enable sub-apps to be overridden,
  oscar classes are loading generically using a special `import_module`
  function.  This looks at the `INSTALLED_APPS` tuple to determine the
  appropriate app to load a class from.

*   **All core views are class-based.**  This enables any view to be subclassed and extended within your project.

*   **Any template can be overridden by a local version**  This is a simple technique relying on the fact
    that the template loader can be configured to look in your project first for oscar templates.