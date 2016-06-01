==========
Test suite
==========

Running tests
-------------

Oscar uses pytest_ to run the tests, which can be invoked using::

    $ ./runtests.py

.. _pytest: http://pytest.org/latest/

You can run a subset of the tests by passing a path:

    $ ./runtests.py tests/unit/offer/availability_tests.py

To run an individual test class, use::

    $ ./runtests.py tests/unit/offer/availability_tests.py::TestASuspendedOffer

(Note the '::'.)

To run an individual test, use::

    $ ./runtests.py tests/unit/offer/availability_tests.py::TestASuspendedOffer::test_is_unavailable

You can also run tests which match an expression via::

    $ ./runtests.py tests/unit/offer/availability_tests.py -k is_unavailable

Testing against different setups
--------------------------------

To run all tests against multiple versions of Django and Python, use detox_::

    $ detox

You need to have all Python interpreters to test against installed on your 
system. All other requirements are downloaded automatically.
detox_ is a wrapper around tox_, creating the environments and running the tests
in parallel. This greatly speeds up the process.

.. _tox: https://tox.readthedocs.io/en/latest/
.. _detox: https://pypi.python.org/pypi/detox

Kinds of tests
--------------

Tests are split into 3 folders:

* unit - These are for tests that exercise a single unit of functionality, like
  a single model.  Ideally, these should not write to the database at all - all
  operations should be in memory.

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

    $ py.test tests/integration/catalogue/product_tests.py --spec
    ============================== test session starts ==============================
    platform darwin -- Python 2.7.9 -- py-1.4.26 -- pytest-2.7.0
    rootdir: /Users/mvantellingen/projects/django-oscar, inifile: setup.cfg
    plugins: cache, cov, django, spec, xdist
    collected 15 items 

    tests/integration/catalogue/product_tests.py::ProductCreationTests
        [PASS]  Allow two products without upc
        [PASS]  Create products with attributes
        [PASS]  None upc is represented as empty string
        [PASS]  Upc uniqueness enforced

    tests/integration/catalogue/product_tests.py::TopLevelProductTests
        [PASS]  Top level products are part of browsable set
        [PASS]  Top level products must have product class
        [PASS]  Top level products must have titles

    tests/integration/catalogue/product_tests.py::ChildProductTests
        [PASS]  Child products are not part of browsable set
        [PASS]  Child products dont need a product class
        [PASS]  Child products dont need titles
        [PASS]  Child products inherit fields
        [PASS]  Have a minimum price

    tests/integration/catalogue/product_tests.py::TestAChildProduct
        [PASS]  Delegates requires shipping logic

    tests/integration/catalogue/product_tests.py::ProductAttributeCreationTests
        [PASS]  Entity attributes
        [PASS]  Validating option attribute

    =========================== 15 passed in 1.64 seconds ===========================


.. _spec: https://pypi.python.org/pypi/pytest-spec
