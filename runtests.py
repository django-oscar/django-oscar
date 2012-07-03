#!/usr/bin/env python
import sys
import logging
from optparse import OptionParser
from coverage import coverage

# This configures the settings
from tests.config import configure
configure()

from django_nose import NoseTestSuiteRunner

logging.disable(logging.CRITICAL)


def run_tests(verbosity, *test_args):
    test_runner = NoseTestSuiteRunner(verbosity=verbosity)
    if not test_args:
        test_args = ['tests']
    num_failures = test_runner.run_tests(test_args)
    if num_failures:
        sys.exit(num_failures)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-c', '--coverage', dest='use_coverage', default=False,
                      action='store_true', help="Generate coverage report")
    parser.add_option('-v', '--verbosity', dest='verbosity', default=1,
                      type='int', help="Verbosity of output")
    (options, args) = parser.parse_args()

    if options.use_coverage:
        print 'Running tests with coverage'
        c = coverage(source=['oscar'])
        c.start()
        run_tests(options.verbosity, *args)
        c.stop()
        print 'Generate HTML reports'
        c.html_report()
    else:
        run_tests(options.verbosity, *args)
