#!/usr/bin/env python
"""
Custom test runner

If args or options, we run the testsuite as quickly as possible.

If args but no options, we default to using the spec plugin and aborting on
first error/failure.

If options, we ignore defaults and pass options onto Nose.

Examples:

Run all tests (as fast as possible)
$ ./runtests.py

Run all unit tests (using spec output)
$ ./runtests.py tests/unit

Run all checkout unit tests (using spec output)
$ ./runtests.py tests/unit/checkout

Run all tests relating to shipping
$ ./runtests.py --attr=shipping

Re-run failing tests (needs to be run twice to first build the index)
$ ./runtests.py ... --failed

Drop into pdb when a test fails
$ ./runtests.py ... --pdb-failures
"""

import sys
import logging
import warnings

from tests.config import configure

# No logging
logging.disable(logging.CRITICAL)

# Warnings: ignore some uninteresting ones but raise an exception on a
# DeprecationWarnings.
warnings.simplefilter('default')
warnings.filterwarnings('error', category=DeprecationWarning)
for category in [PendingDeprecationWarning, UserWarning, ImportWarning]:
    warnings.filterwarnings('ignore', category=category)



def run_tests(*test_args):
    from django_nose import NoseTestSuiteRunner
    test_runner = NoseTestSuiteRunner()
    if not test_args:
        test_args = ['tests']
    num_failures = test_runner.run_tests(test_args)
    if num_failures:
        sys.exit(num_failures)


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args:
        import multiprocessing
        try:
            num_cores = multiprocessing.cpu_count()
        except NotImplementedError:
            num_cores = 4
        args = ['-s', '-x', '--processes=%s' % num_cores]
    else:
        # Some args specified.  Check to see if any nose options have been
        # specified.  If they have, then don't set any
        has_options = any(map(lambda x: x.startswith('--'), args))
        if not has_options:
            args.extend(['-s', '-x', '--with-specplugin'])
        else:
            # Remove options as nose will pick these up from sys.argv
            args = [arg for arg in args if not arg.startswith('-')]

    configure()
    run_tests(*args)
