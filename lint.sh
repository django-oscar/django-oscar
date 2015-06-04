#!/usr/bin/env bash
#
# Run static analysis of the codebase
#
# This is run on Travis to ensure that pull requests conform to the project coding standards.

# Ideally, this figure should be 0. But to keep the amount of "Fix PEP8" commits
# low, we only fail Travis after a certain amount of warnings have accumulated
THRESHOLD=16

# Run flake8 and convert the output into a format that the "violations" plugin 
# for Jenkins/Hudson can understand.
# flake8 is configured in [flake8] section in tox.ini
ERROR_FILE="violations.txt"
flake8 src/oscar | perl -ple "s/: /: [E] /" > $ERROR_FILE
cat $ERROR_FILE

# Check that the number of violations is acceptable
NUMERRORS=`cat $ERROR_FILE | wc -l`
if [ $NUMERRORS -gt $THRESHOLD ]
then
    echo "Too many flake8 errors - maximum allowed is $THRESHOLD, found $NUMERRORS"
    exit 1
fi
