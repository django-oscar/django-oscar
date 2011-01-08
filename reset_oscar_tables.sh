#!/bin/bash
# For dropping and recreating all the oscar tables
# @todo rewrite this a manage.py command
./manage.py sqlclear  payment offer order basket stock product | ./manage.py dbshell && \
./manage.py syncdb