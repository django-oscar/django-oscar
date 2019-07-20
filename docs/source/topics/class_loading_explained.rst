===============================
Dynamic class loading explained
===============================

Dynamic class loading is the foundation for making Oscar extensively
customisable. It is hence worth understanding how it works, because most
customisation depends on it.

It is achieved by :meth:`oscar.core.loading.get_classes` and its
single-class cousin :meth:`~oscar.core.loading.get_class`.  Wherever feasible,
Oscar uses ``get_classes`` instead of a regular import statement:

.. code-block:: python

    from oscar.apps.shipping.repository import Repository

is replaced by:

.. code-block:: python

    from oscar.core.loading import get_class

    Repository = get_class('shipping.repository', 'Repository')

.. note:: This is done for almost all classes: views, models, etc. Every class
          imported by ``get_class`` can be overridden.

Why?
----

This structure enables a project to create a local ``shipping.repository``
module, and optionally subclass the class from
``oscar.apps.shipping.repository``.  When Oscar tries to load the
``Repository`` class, it will load the one from your local project.

This way, most classes can be overridden with minimal duplication, as only
the to-be-changed classes have to be altered. They can optionally inherit from
Oscar's implementation, which often amounts to little more than a few lines of
custom code for changes to core behaviour.

Seen on a bigger scale, this structures enables Oscar to ship with classes with
minimal assumptions about the domain, and make it easy to modify behaviour as
needed.

How it works
------------

The ``get_class`` function looks through your ``INSTALLED_APPS`` for a matching
app and will attempt to load the custom class from the specified module. If the
app isn't overridden or the custom module doesn't define the class, it will
fall back to the default Oscar class.

In practice
-----------

For ``get_class`` to pick up the customised class, the Oscar apps need to be
forked. The process is detailed and illustrated with examples in
:doc:`/topics/customisation`. It is usually enough to call ``oscar_fork_app``
and replace the app in ``INSTALLED_APPS``.

Using ``get_class`` in your own code
------------------------------------

Generally, there is no need for ``get_class`` in your own code as the location
of the module for the class is known. Some Oscar developers nonetheless
use ``get_class`` when importing classes from Oscar. This means that if someday
the class is overridden, it will not require code changes. Care should be taken
when doing this, as this is a tricky trade-off between maintainability and
added complexity.
Please note that we cannot recommend ever using ``get_model`` in your own code.
Model initialisation is a tricky process and it's
easy to run into circular import issues.


Overriding dynamic class loading behaviour
------------------------------------

In some cases it may be necessary to customise the logic used by Oscar to
dynamically load classes. You can do this by supplying your own class loader
function to the ``OSCAR_DYNAMIC_CLASS_LOADER`` setting:

.. code-block:: python

    OSCAR_DYNAMIC_CLASS_LOADER = 'myproject.custom_class_loader'

Supply a dotted Python path to a callable that takes
the same arguments as :meth:`~oscar.core.loading.default_class_loader`.


Testing
-------

You can test whether your overriding worked by trying to get a class from your
module:

.. code-block:: python

    >>> from oscar.core.loading import get_class
    >>> get_class('shipping.repository', 'Repository')
    yourproject.shipping.repository.Repository  # it worked!
