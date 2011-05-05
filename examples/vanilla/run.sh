#!/bin/bash

# Set sleep period as first argument, defaults to 30 seconds
SLEEP_PERIOD=$1
: ${SLEEP_PERIOD:=30}

while true; do
	./manage.py test oscar --settings=test_settings
	sleep $SLEEP_PERIOD
done