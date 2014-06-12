#!/bin/bash
#
# Build a docker container of the Oscar sandbox site
#
# This script exists as running "docker build ." in the root of the Oscar repo
# is REALLY SLOW as it uploads everything under the root (the "context" which
# is ~1Gb) to the boot2docker VM (on OSX that is). We work around this by
# copying only the things we need into a temp folder and running "docker build"
# from there.

# The image repo can be optionally passed in
REPO=${1:-django_oscar_sandbox}

# Change to directory of this script
cd "$(dirname "$0")"

# Clean things up before we start
(cd .. && make clean)

TMP_DIR=$(mktemp -d)
echo "Creating context in $TMP_DIR"
TO_COPY=(
    Dockerfile
    apt-packages.txt
    supervisord.conf
    cronfile
    ../README.rst
    ../setup.py
    ../requirements.txt
    ../Makefile
    ../oscar
    ../sites
)
cp -r ${TO_COPY[@]} $TMP_DIR

# Use docker-specific local settings
mv $TMP_DIR/sites/sandbox/settings_{docker,local}.py

echo "Building docker container named $REPO"
cd $TMP_DIR
docker build --rm=true -t $REPO .

echo "Removing temp folder $TMP_DIR"
rm -rf $TMP_DIR

echo
echo "You can now run this container using"
echo
echo "$ docker run -P $REPO"
echo
echo "See the output of 'docker ps' to see which host port is being used"
if [[ `uname` -eq "Darwin" ]]; 
then
    echo
    echo "OSX users will also need to port forward from the boot2docker VM"
    echo "See https://github.com/boot2docker/boot2docker/blob/master/doc/WORKAROUNDS.md"
fi
