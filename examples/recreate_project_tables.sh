#!/usr/bin/env bash
# For dropping and recreating all tables of a specified shop

if [ $# -ne 1 ] 
then
	printf "Please specify a project folder\n"
	exit 1
fi
PROJECT_FOLDER=`basename $1`
MANAGE_COMMAND=$PROJECT_FOLDER/manage.py
if [ ! -f $MANAGE_COMMAND ]
then
	printf "$MANAGE_COMMAND cannot be found\n"
fi
echo "Recreating all tables in $PROJECT_FOLDER"
echo "Dropping tables"
$MANAGE_COMMAND sqlclear customer promotions analytics payment reviews offer shipping order basket partner address catalogue datacash | \
	awk 'BEGIN {print "set foreign_key_checks=0;"} {print $0}' | \
    $MANAGE_COMMAND dbshell && \
    $MANAGE_COMMAND syncdb
