#!/usr/bin/env python
import sys
import logging

from tests.config import configure

logging.disable(logging.CRITICAL)


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
