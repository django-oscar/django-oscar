#!/usr/bin/env python
import sys
import os
import logging
from optparse import OptionParser

import tests.config

from django.test.simple import DjangoTestSuiteRunner

logging.disable(logging.CRITICAL)


def run_tests(*test_args):
    test_runner = DjangoTestSuiteRunner(verbosity=1)
    if not test_args:
        test_args = ['oscar']
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    run_tests(*args)
