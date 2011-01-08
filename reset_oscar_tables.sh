#!/bin/bash
# For dropping and recreating all the oscar tables
# @todo rewrite this a manage.py command
./manage.py sqlclear basket payment offer order product | ./manage.py dbshell
./manage.py syncdb