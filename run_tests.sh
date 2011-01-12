#!/bin/bash
# Test runnner script that specifies correct settings file
# and filters out useless output
time ./manage.py test oscar --settings=test_settings -v 1 --failfast | \
	grep -v "^\(Installing\|Creating\)"
