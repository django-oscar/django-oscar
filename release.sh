#!/bin/bash

RELEASE_NUM=`./setup.py --version`
git tag | grep $RELEASE_NUM > /dev/null && \
	echo "New version number required ($RELEASE_NUM already used)" && exit 1

# Push to PyPi
./setup.py sdist upload

# Tag in Git
git tag $RELEASE_NUM -m "Tagging release $RELEASE_NUM"
git push --tags