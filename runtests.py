#!/usr/bin/env python
import sys
import logging

from tests.config import configure

logging.disable(logging.CRITICAL)


def run_tests(verbosity, *test_args):
    from django_nose import NoseTestSuiteRunner
    test_runner = NoseTestSuiteRunner(verbosity=verbosity)
    if not test_args:
        test_args = ['tests']
    num_failures = test_runner.run_tests(test_args)
    if num_failures:
        sys.exit(num_failures)


if __name__ == '__main__':
    args = sys.argv[1:]

    verbosity = 1
    if not args:
        # If run with no args, try and run the testsuite as fast as possible.
        # That means across all cores and with no high-falutin' plugins.
        import multiprocessing
        try:
            num_cores = multiprocessing.cpu_count()
        except NotImplementedError:
            num_cores = 4  # Guess
        args = ['--nocapture', '--stop', '--processes=%s' % num_cores]
    else:
        # Some args/options specified.  Check to see if any nose options have
        # been specified.  If they have, then don't set any
        has_options = any(map(lambda x: x.startswith('--'), args))
        if not has_options:
            # Default options:
            # --stop Abort on first error/failure
            # --nocapture Don't capture STDOUT
            args.extend(['--nocapture', '--stop', '--with-specplugin'])
        else:
            # Remove options as nose will pick these up from sys.argv
            for arg in args:
                if arg.startswith('--verbosity'):
                    verbosity = int(arg[-1])
            args = [arg for arg in args if not arg.startswith('-')]

    configure()
    run_tests(verbosity, *args)
