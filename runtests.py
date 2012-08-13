#!/usr/bin/env python
import sys
import logging
from optparse import OptionParser

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
    parser = OptionParser()
    __, args = parser.parse_args()

    # If no args, then use 'progressive' plugin to keep the screen real estate
    # used down to a minimum.  Otherwise, use the spec plugin
    nose_args = ['-s', '-x',
                 '--with-progressive' if not args else '--with-spec']
    #nose_args.extend([
    #    '--with-coverage', '--cover-package=oscar', '--cover-html',
    #    '--cover-html-dir=htmlcov'])
    configure(nose_args)
    run_tests(*args)
