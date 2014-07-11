#!/bin/bash
#
# Build a docker container of the Oscar demo site

# The image repo can be optionally passed in
REPO=${1:-django_oscar_demo}

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
mv $TMP_DIR/sites/demo/settings_{docker,local}.py

echo "Building docker container named $REPO"
cd $TMP_DIR
docker build --rm=true --tag=$REPO .

echo "Removing temp folder $TMP_DIR"
rm -rf $TMP_DIR
