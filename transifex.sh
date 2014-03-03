#!/usr/bin/env bash
#
# Push source and translation files to Transifex.
#
# This script is called after every successful build on Travis CI.
# It relies on $TRANSIFEX_PASSWORD being set in .travis.yml

# Only run once, and only on master
echo $TRAVIS_JOB_NUMBER | grep "\.1$"
if [ $? -eq 0 ] && [ $TRAVIS_BRANCH == master ]
then
    echo "Submitting translation files to Transifex"
    make messages
    pip install "transifex-client==0.10"
    # Write .transifexrc file
    echo "[https://www.transifex.com]
hostname = https://www.transifex.com
password = $TRANSIFEX_PASSWORD
token =
username = oscar_bot" > ~/.transifexrc
    tx push --source --translations --no-interactive --skip
fi
