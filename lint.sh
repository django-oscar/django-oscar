#/usr/bin/env bash
#
# Run static analysis of the codebase
#
# This is run on Travis to ensure that pull requests conform to the project coding standards.

# Run flake8 and convert the output into a format that the "violations" plugin 
# for Jenkins/Hudson can understand.  Ignore warnings from migrations we we don't
# really care about those.
ERRORFILE="violations.txt"
flake8 --exclude=migrations oscar | perl -ple "s/: /: [E] /" > $ERRORFILE

# Check that the number of violations is acceptable
NUMERRORS=`cat $ERRORFILE | wc -l`
if [ $NUMERRORS -gt 0 ]
then
    cat violations.txt
    exit 1
fi
