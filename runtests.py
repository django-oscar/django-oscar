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
    parser.add_option('--with-coverage', dest='coverage', default=False,
                      action='store_true')
    parser.add_option('--with-xunit', dest='xunit', default=False,
                      action='store_true')
    parser.add_option('--collect-only', dest='collect', default=False,
                      action='store_true')
    options, args = parser.parse_args()

    if options.collect:
        # Show tests only so a bash autocompleter can use the results
        configure(['-v'])
        run_tests()
    else:
        # If no args, then use 'progressive' plugin to keep the screen real
        # estate used down to a minimum.  Otherwise, use the spec plugin
        nose_args = ['-s', '-x']
        if args:
            nose_args.extend(['--with-specplugin'])
        else:
            nose_args.append('--with-progressive')

        if options.coverage:
            # Nose automatically uses any options passed to runtests.py, which
            # is why the coverage trigger uses '--with-coverage' and why we
            # don't need to explicitly include it here.
            nose_args.extend([
                '--cover-package=oscar', '--cover-html',
                '--cover-html-dir=htmlcov'])
        configure(nose_args)
        run_tests(*args)
