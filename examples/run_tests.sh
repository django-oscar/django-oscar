#!/usr/bin/env bash
# For running all tests

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
echo "Running all tests in $PROJECT_FOLDER"
time $MANAGE_COMMAND test oscar --settings=test_settings -v 1 --failfast | \
	grep -v "^\(Installing\|Creating\)"

