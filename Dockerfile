FROM ubuntu
MAINTAINER david.winterbottom@tangentlabs.co.uk

# Ensure whole repo is available in container
ADD ./ /code/

RUN apt-get update -qq

# Install a load of packages
RUN cat /code/apt-packages.txt | xargs apt-get --force-yes install
