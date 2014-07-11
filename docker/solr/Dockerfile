FROM ubuntu:14.04

MAINTAINER david.winterbottom@tangentlabs.co.uk

ENV VERSION 4.8.1

# Install Solr 
RUN apt-get update -qq --fix-missing
RUN apt-get install -y wget default-jre-headless
RUN wget -q http://www.mirrorservice.org/sites/ftp.apache.org/lucene/solr/$VERSION/solr-$VERSION.tgz 
RUN tar --extract --file solr-$VERSION.tgz -C /opt
RUN ln -s /opt/solr-$VERSION /opt/solr
RUN rm -rf /opt/solr/example/solr/collection1/conf

# Link in Solr conf
ADD ./ /code/
RUN ln -s /code/solr /opt/solr/example/solr/collection1/conf

WORKDIR /opt/solr-$VERSION/example

EXPOSE 8983

CMD ["echo", "hello"]
