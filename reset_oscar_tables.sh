#!/bin/bash
# For dropping and recreating all the oscar tables
# @todo rewrite this a manage.py command
echo "Dropping tables"
./manage.py sqlclear payment offer order basket stock image product | \
	awk 'BEGIN {print "set foreign_key_checks=0;"} {print $0}' | \
    ./manage.py dbshell && \
    ./manage.py syncdb
