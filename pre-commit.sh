#!/usr/bin/env bash

git stash --keep-index -q

source ~/.virtualenvs/oscar/bin/activate

./runtests.py
TEST_RESULT=$?

jshint oscar/static/oscar/js/oscar
JS_RESULT=$?

FILES_PATTERN='\.(py)(\..+)?$'
FORBIDDEN='assert False'
GREP_RESULT=1
FILES=`git diff --cached --name-only | grep -E $FILES_PATTERN`
if [ $? -eq 0 ]; then
	echo $FILES | xargs grep --color --with-filename -n "$FORBIDDEN"
	GREP_RESULT=$?
fi

git stash pop -q

[ $TEST_RESULT -ne 0 ] && echo "Tests failed" && exit 1
[ $JS_RESULT -ne 0 ] && echo "JShint failed" && exit 1
[ $GREP_RESULT -eq 0 ] && echo "Found 'assert False'" && exit 1

exit 0
