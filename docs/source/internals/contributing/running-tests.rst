==========
Test suite
==========

Testing requirements
--------------------

You'll need:

- A running SQL server (PostgreSQL, or SQLite with `--sqlite` parameters)
- python3.7 or higher.

Running tests
-------------

Oscar uses pytest_ to run the tests.

The fast way is::

    $ make test

This will create a virtualenv in `venv`, install the test dependencies and run
pytest_.

.. _pytest: http://pytest.org/latest/

Details
~~~~~~~

First we create a virtualenv, install the required dependencies and activate it::

    $ make venv
    $ source venv/bin/activate

Then we run the test suite using::

    $ py.test

You can run a subset of the tests by passing a path::

    $ py.test tests/integration/offer/test_availability.py

To run an individual test class, use::

    $ py.test tests/integration/offer/test_availability.py::TestASuspendedOffer

(Note the '::'.)

To run an individual test, use::

    $ py.test tests/integration/offer/test_availability.py::TestASuspendedOffer::test_is_unavailable

You can also run tests which match an expression via::

    $ py.test tests/integration/offer/test_availability.py -k is_unavailable

Testing against different setups
--------------------------------

To run all tests against multiple versions of Django and Python, use tox_::

    $ tox

You need to have all Python interpreters to test against installed on your
system. All other requirements are downloaded automatically.

To speed up the process, you may want to use `tox parallel mode`_.

.. _tox: https://tox.readthedocs.io/en/latest/
.. _tox parallel mode: https://tox.readthedocs.io/en/latest/example/basic.html#parallel-mode

Kinds of tests
--------------

Tests are split into 3 folders:

* integration - These are for tests that exercise a collection or chain of
  units, like testing a template tag.

* functional - These should be as close to "end-to-end" as possible.  Most of
  these tests should use WebTest to simulate the behaviour of a user browsing
  the site.

Naming tests
------------

When running a subset of tests, Oscar uses the spec_ plugin.  It is a good
practice to name your test cases and methods so that the spec output reads well.
For example::

    $ py.test tests/integration/catalogue/test_product.py --spec
    ============================ test session starts =============================
    platform darwin -- Python 3.6.0, pytest-3.0.6, py-1.4.33, pluggy-0.4.0
    rootdir: /Users/sasha0/projects/djangooscar, inifile: setup.cfg
    plugins: xdist-1.15.0, warnings-0.2.0, spec-1.1.0, django-3.1.2, cov-2.4.0
    collected 15 items

    tests/integration/catalogue/test_product.py::ProductCreationTests
        [PASS]  Allow two products without upc
        [PASS]  Create products with attributes
        [PASS]  None upc is represented as empty string
        [PASS]  Upc uniqueness enforced

    tests/integration/catalogue/test_product.py::TopLevelProductTests
        [PASS]  Top level products are part of browsable set
        [PASS]  Top level products must have product class
        [PASS]  Top level products must have titles

    tests/integration/catalogue/test_product.py::ChildProductTests
        [PASS]  Child products are not part of browsable set
        [PASS]  Child products dont need a product class
        [PASS]  Child products dont need titles
        [PASS]  Child products inherit fields

    tests/integration/catalogue/test_product.py::TestAChildProduct
        [PASS]  Delegates requires shipping logic

    tests/integration/catalogue/test_product.py::ProductAttributeCreationTests
        [PASS]  Entity attributes
        [PASS]  Validating option attribute

    tests/integration/catalogue/test_product.py::ProductRecommendationTests
        [PASS]  Recommended products ordering

    ========================= 15 passed in 15.39 seconds =========================

.. _spec: https://pypi.python.org/pypi/pytest-spec
