#!/usr/bin/env python
import sys
import logging
from optparse import OptionParser
from coverage import coverage

from tests.config import configure

logging.disable(logging.CRITICAL)


def run_tests(options, *test_args):
    from django_nose import NoseTestSuiteRunner
    test_runner = NoseTestSuiteRunner(verbosity=options.verbosity,
                                      pdb=options.pdb,
                                      )
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
    parser.add_option('-d', '--pdb', dest='pdb', default=False,
                      action='store_true', help="Whether to drop into PDB on failure/error")
    (options, args) = parser.parse_args()

    # If no args, then use 'progressive' plugin to keep the screen real estate
    # used down to a minimum.  Otherwise, use the spec plugin
    nose_args = ['-s', '-x',
                 '--with-progressive' if not args else '--with-spec']
    configure(nose_args)

    if options.use_coverage:
        print 'Running tests with coverage'
        c = coverage(source=['oscar'])
        c.start()
        run_tests(options, *args)
        c.stop()
        print 'Generate HTML reports'
        c.html_report()
    else:
        run_tests(options, *args)
