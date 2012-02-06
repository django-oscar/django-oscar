#!/usr/bin/env bash

source ~/.virtualenvs/oscar/bin/activate
./run_tests.py
[ $? -ne 0 ] && echo "Tests failed" && exit 1

exit 0
