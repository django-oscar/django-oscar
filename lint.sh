#/usr/bin/env bash

ERRORFILE="violations.txt"
THRESHOLD=1050
IGNORE="W292,E202"

flake8 --ignore=$IGNORE oscar | perl -ple "s/: /: [E] /" | grep -v migrations > $ERRORFILE

# Check that the number of violations is acceptable
NUMERRORS=`cat $ERRORFILE | wc -l`
if [ $NUMERRORS -gt $THRESHOLD ]
then
	echo 
	echo "Too many flake8 errors - maximum allowed is $THRESHOLD, found $NUMERRORS"
	echo 
	echo "To fix, run 'make lint' and examine $ERRORFILE"
	exit 1
fi
