==========
Test suite
==========

Running tests
-------------

Oscar uses a nose_ testrunner which can be invoked using::

    $ ./runtests.py

.. _nose: http://nose.readthedocs.org/en/latest/

To run a subset of tests, you can use filesystem or module paths.  These two
commands will run the same set of tests::

    $ ./runtests.py tests/unit/offer/availability_tests.py
    $ ./runtests.py tests.unit.offer.availability_tests

To run an individual test class, use one of::

    $ ./runtests.py tests/unit/offer/availability_tests.py:TestAPerUserConditionalOffer
    $ ./runtests.py tests.unit.offer.availability_tests:TestAPerUserConditionalOffer

(Note the ':'.)

To run an individual test, use one of::

    $ ./runtests.py tests/unit/offer/availability_tests.py:TestAPerUserConditionalOffer.test_is_available_with_no_applications
    $ ./runtests.py tests.unit.offer.availability_tests:TestAPerUserConditionalOffer.test_is_available_with_no_applications

To check if the number of queries changes::

    $ ./runtests.py --with-querycount

Please note that ``--with-querycount`` sets ``DEBUG = True``, which might affect
test outcomes. Total query count gives a quick indication. Diff'ing the outputs
is recommended for further analysis.

Testing against different setups
--------------------------------

To run all tests against multiple versions of Django and Python, use detox_::

    $ detox

You need to have all Python interpreters to test against installed on your 
system. All other requirements are downloaded automatically.
detox_ is a wrapper around tox_, creating the environments and running the tests
in parallel. This greatly speeds up the process.

.. _tox: http://tox.readthedocs.org/en/latest/
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

    $ ./runtests.py tests/unit/offer/benefit_tests.py:TestAbsoluteDiscount
    nosetests --verbosity 1 tests/unit/offer/benefit_tests.py:TestAbsoluteDiscount -s -x --with-spec
    Creating test database for alias 'default'...

    Absolute discount
    - consumes all lines for multi item basket cheaper than threshold
    - consumes all products for heterogeneous basket
    - consumes correct quantity for multi item basket more expensive than threshold
    - correctly discounts line
    - discount is applied to lines
    - gives correct discount for multi item basket cheaper than threshold
    - gives correct discount for multi item basket more expensive than threshold
    - gives correct discount for multi item basket with max affected items set
    - gives correct discount for single item basket cheaper than threshold
    - gives correct discount for single item basket equal to threshold
    - gives correct discount for single item basket more expensive than threshold
    - gives correct discounts when applied multiple times
    - gives correct discounts when applied multiple times with condition
    - gives no discount for a non discountable product
    - gives no discount for an empty basket

    ----------------------------------------------------------------------
    Ran 15 tests in 0.295s

.. _spec: https://github.com/bitprophet/spec
