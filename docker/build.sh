#!/bin/bash
#
# Build a docker container of the Oscar sandbox site
#
# This script exists as running "docker build ." in the root of the Oscar repo
# is REALLY SLOW as it uploads everything under the root (the "context" which
# is ~1Gb) to the boot2docker VM (on OSX that is). We work around this by
# copying only the things we need into a temp folder and running "docker build"
# from there.

# The image tag can be optionally passed in
TAG=${1:-oscar_latest}

# Change to directory of this script
cd "$(dirname "$0")"

# Clean things up before we start
(cd .. && make clean)

TMP_DIR=$(mktemp -d)
echo "Creating context in $TMP_DIR"
TO_COPY=(
    Dockerfile
    apt-packages.txt
    ../README.rst
    ../setup.py
    ../requirements.txt
    ../Makefile
    ../oscar
    ../sites
)
cp -r ${TO_COPY[@]} $TMP_DIR

echo "Building docker container tagged $TAG"
cd $TMP_DIR
IMAGE_ID=$(docker build -t $TAG .)

echo "Removing temp folder $TMP_DIR"
rm -rf $TMP_DIR

echo "You can now run the Django server within this container by doing this"
echo "$ docker run -it -p 8000:8000 $TAG /code/sites/sandbox/runserver 0.0.0.0:8000"
if [[ `uname` -eq "Darwin" ]]; 
then
    echo "You will also need to forward port 8000 of the boot2docker VM"
    echo "See https://github.com/boot2docker/boot2docker/blob/master/doc/WORKAROUNDS.md"
fi
