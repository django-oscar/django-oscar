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
REPO=${1:-django_oscar_solr}

# Change to directory of this script
cd "$(dirname "$0")"

TMP_DIR=$(mktemp -d)
echo "Creating context in $TMP_DIR"
TO_COPY=(
    Dockerfile
    ../../sites/sandbox/deploy/solr
)
cp -r ${TO_COPY[@]} $TMP_DIR
cd $TMP_DIR

echo "Building docker container named $REPO"
docker build --rm=true --tag=$REPO .

echo "Removing temp folder $TMP_DIR"
rm -rf $TMP_DIR
