#!/usr/bin/env python
"""
Custom test runner

If args or options, we run the testsuite as quickly as possible.

If args but no options, we default to using the spec plugin and aborting on
first error/failure.

If options, we ignore defaults and pass options onto pytest.

Examples:

Run all tests (as fast as possible)
$ ./runtests.py

Run all unit tests (using spec output)
$ ./runtests.py tests/unit

Run all checkout unit tests (using spec output)
$ ./runtests.py tests/unit/checkout

Re-run failing tests (requires pytest-cache)
$ ./runtests.py ... --lf

Drop into pdb when a test fails
$ ./runtests.py ... --pdb
"""

import os
import multiprocessing
import sys
import logging
import warnings

import pytest
from django.utils.six.moves import map

# No logging
logging.disable(logging.CRITICAL)


if __name__ == '__main__':
    args = sys.argv[1:]

    verbosity = 1
    if not args:
        # If run with no args, try and run the testsuite as fast as possible.
        # That means across all cores and with no high-falutin' plugins.

        try:
            cpu_count = int(multiprocessing.cpu_count())
        except ValueError:
            cpu_count = 1

        args = [
            '--capture=no', '--nomigrations', '-n=%d' % cpu_count,
            'tests'
        ]
    else:
        # Some args/options specified.  Check to see if any options have
        # been specified.  If they have, then don't set any
        has_options = any(map(lambda x: x.startswith('--'), args))
        if not has_options:
            # Default options:
            # --exitfirst Abort on first error/failure
            # --capture=no Don't capture STDOUT
            args.extend(['--capture=no', '--nomigrations', '--exitfirst'])
        else:
            args = [arg for arg in args if not arg.startswith('-')]

    with warnings.catch_warnings():
        # The warnings module in default configuration will never cause tests
        # to fail, as it never raises an exception.  We alter that behaviour by
        # turning DeprecationWarnings into exceptions, but exclude warnings
        # triggered by third-party libs. Note: The context manager is not
        # thread safe. Behaviour with multiple threads is undefined.
        warnings.filterwarnings('error', category=DeprecationWarning)
        warnings.filterwarnings('error', category=RuntimeWarning)
        libs = r'(sorl\.thumbnail.*|bs4.*|webtest.*|inspect.*|re.*)'
        warnings.filterwarnings(
            'ignore', r'.*', DeprecationWarning, libs)

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
        result_code = pytest.main(args)
        sys.exit(result_code)
