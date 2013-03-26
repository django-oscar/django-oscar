#!/bin/bash

# Check to see if the version number has been bumped
RELEASE_NUM=`./setup.py --version`
git tag | grep $RELEASE_NUM > /dev/null && \
	echo "New version number required ($RELEASE_NUM already used)" && exit 1

# Update CSS from LESS
make css

# Push to PyPi
./setup.py sdist upload

# Tag in Git and push everything up
git tag $RELEASE_NUM -m "Tagging release $RELEASE_NUM"
git push --tags
git push 
