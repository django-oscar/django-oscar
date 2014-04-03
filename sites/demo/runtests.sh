#!/usr/bin/env bash
#
# Run the project tests

# Change to directory of this script
cd "$( dirname "$0" )"

TESTS=${1:-"tests"}
shift
python manage.py test $TESTS --settings=settings_test --noinput $@

# Print out a nice colored message
if [ $? -eq 0 ]; then
    echo -e "\033[42;37m\nTests passed!\033[0m"
else
    echo -e "\033[41;37m\nTests failed!\033[0m"
    exit 1
fi
