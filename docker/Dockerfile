FROM ubuntu

MAINTAINER david.winterbottom@tangentlabs.co.uk

# Copy code into container
ADD ./ /code/

# Install a load of packages
RUN apt-get update -qq
RUN cat /code/apt-packages.txt | xargs apt-get -y --force-yes install

# Upgrade pip
RUN pip install -U pip

# Install python deps (note, no need for a virtualenv inside a container) and
# build the sandbox database.
RUN cd /code && make sandbox

# Forward port 8000 so we can interact with Django's server running within
# the container.
EXPOSE 8000
