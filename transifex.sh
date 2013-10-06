#!/usr/bin/env bash
# pushes source and translation files to Transifex
# called after every successful build on Travis CI
# relies on $TRANSIFEX_PASSWORD being set in .travis.yml

# only run once, and only on master
echo $TRAVIS_JOB_NUMBER | grep "\.1$"
if [ $? -eq 0 ] && [ $TRAVIS_BRANCH == master ]
  then
    make messages
    # write .transifexrc file
    echo "[https://www.transifex.com]
hostname = https://www.transifex.com
password = $TRANSIFEX_PASSWORD
token =
username = oscar_bot" > ~/.transifexrc
    tx push --source --translations --no-interactive
fi

