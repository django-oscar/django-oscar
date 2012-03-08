#!/usr/bin/env bash

git stash --keep-index -q

source ~/.virtualenvs/oscar/bin/activate

./run_tests.py
TEST_RESULT=$?

jshint oscar/static/js/oscar
JS_RESULT=$?

git stash pop -q

[ $TEST_RESULT -ne 0 ] && echo "Tests failed" && exit 1
[ $JS_RESULT -ne 0 ] && echo "JShint failed" && exit 1

exit 0
