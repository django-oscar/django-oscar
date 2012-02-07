#!/usr/bin/env python
import sys
import os
import logging
from optparse import OptionParser
from coverage import coverage

import tests.config

from django.test.simple import DjangoTestSuiteRunner

logging.disable(logging.CRITICAL)


def run_tests(*test_args):
    test_runner = DjangoTestSuiteRunner(verbosity=1)
    if not test_args:
        test_args = ['oscar']
    num_failures = test_runner.run_tests(test_args)
    if num_failures:
        sys.exit(num_failures)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-c', '--coverage', dest='use_coverage', default=False,
                      action='store_true', help="Generate coverage report")
    (options, args) = parser.parse_args()

    if options.use_coverage:
        print 'Running tests with coverage'
        c = coverage(source=['oscar'])
        c.start()
        run_tests(*args)
        c.stop()
        print 'Generate HTML reports'
        c.html_report()
    else:
        print 'Running tests'
        run_tests(*args)
