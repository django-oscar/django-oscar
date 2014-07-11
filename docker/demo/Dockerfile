FROM ubuntu:14.04

MAINTAINER david.winterbottom@tangentlabs.co.uk

RUN apt-get update -qq

# Ensure locale is right before installing Postgres
RUN locale-gen --no-purge en_US.UTF-8
ENV LC_ALL en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8

RUN apt-get install -y postgresql-server-dev-9.3 postgresql-9.3-postgis-2.1
