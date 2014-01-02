#/usr/bin/env bash
#
# Run static analysis of the codebase
#
# This is run on Travis to ensure that pull requests conform to the project coding standards.

# Run flake8 and convert the output into a format that the "violations" plugin 
# for Jenkins/Hudson can understand.  Ignore warnings from migrations we we don't
# really care about those.
ERROR_FILE="violations.txt"
THRESHOLD=0
flake8 --max-complexity=10 oscar | perl -ple "s/: /: [E] /" > $ERROR_FILE

# Check that the number of violations is acceptable
NUMERRORS=`cat $ERROR_FILE | wc -l`
if [ $NUMERRORS -gt $THRESHOLD ]
then
    echo "The following flake8 errors need to be fixed"
    cat $ERROR_FILE
    exit 1
fi
