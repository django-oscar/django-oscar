=====================
Writing documentation
=====================

Directory Structure
-------------------

The docs are built by calling ``make docs`` from your Oscar directory.
They live in ``/docs/source``. 

* ``ref/`` is the reference documentation covering apps, management commands,
  signals, settings and template tags.

* ``topics/`` will contain "meta" articles, explaining how things tie together
  over several apps, or how Oscar can be combined with other solutions.

* ``howto/`` contains tutorial-style descriptions on how to solve a certain
  problem.

* ``contributing/`` contains guidance for contributors

* ``releases/`` contains release notes

Style guides
------------

Oscar currently does not have it's own style guide for writing documentation.
Please carefully review style guides for `Python`_ and `Django`_.

.. _`Python`: http://docs.python.org/devguide/documenting.html#style-guide
.. _`Django`: https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/
