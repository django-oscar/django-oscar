=====================
Writing documentation
=====================

Directory Structure
-------------------

The docs are built by calling ``make docs`` from your Oscar directory.
The ``make docs`` command currently uses `python3`,
so make sure it links to one of these versions.

They live in ``/docs/source``. This directory structure is a
simplified version of what Django does.

* ``internals/`` contains everything related to Oscar itself, e.g. contributing
  guidelines or design philosophies.
* ``ref/`` is the reference documentation, esp. consisting of
* ``ref/apps/`` which should be a guide to each Oscar core app, explaining it's
  function, the main models, how it relates to the other apps, etc.
* ``topics/`` will contain "meta" articles, explaining how things tie together
  over several apps, or how Oscar can be combined with other solutions.
* ``howto/`` contains tutorial-style descriptions on how to solve a certain
  problem.

``/index.rst`` is designed as the entry point, and diverges from above
structure to make the documentation more approachable. Other ``index.rst``
files should only be created if there's too many files to list them all.
E.g. ``/index.rst`` directly links to all files in ``topics/`` and
``internals/``, but there's an ``index.rst`` both for the files in ``howto/``
and ``ref/apps/``.

Style guides
------------
Oscar currently does not have it's own style guide for writing documentation.
Please carefully review style guides for `Python`_ and `Django`_.
Please use `gender-neutral language`_.

.. _`Python`: http://docs.python.org/devguide/documenting.html#style-guide
.. _`Django`: https://docs.djangoproject.com/en/stable/internals/contributing/writing-documentation/
.. _`gender-neutral language`: https://alexgaynor.net/2013/nov/30/gender-neutral-language-faq/
