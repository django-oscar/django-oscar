FROM ubuntu

MAINTAINER david.winterbottom@tangentlabs.co.uk

# Copy code into container
ADD ./ /code/

# Install a load of packages
RUN apt-get update -qq
RUN cat /code/apt-packages.txt | xargs apt-get --yes --force-yes install

# Install Solr manually and symlink in our Solr conf
RUN wget -q http://www.mirrorservice.org/sites/ftp.apache.org/lucene/solr/4.8.1/solr-4.8.1.tgz 
RUN tar --extract --file solr-4.8.1.tgz -C /opt
RUN ln -s /opt/solr-4.8.1 /opt/solr
RUN rm -rf /opt/solr/example/solr/collection1/conf
RUN ln -s /code/sites/sandbox/deploy/solr /opt/solr/example/solr/collection1/conf

# Install python deps (note, no need for a virtualenv inside a container) and
# build the sandbox database.
RUN pip install -U pip
RUN cd /code && make sandbox_base

# Forward port 8000 so we can interact with Django's server running within
# the container.
EXPOSE 8000 8983

# Put cronjob in place
RUN mv /code/cronfile /etc/cron.d/
RUN chmod 600 /etc/cron.d/cronfile

# Run supervisor once the container is built
RUN mv /code/supervisord.conf /etc/supervisor/conf.d/
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
