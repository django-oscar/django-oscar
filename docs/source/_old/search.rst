.. _solr-debian-installing:

Search within Oscar
*******************

Oscar makes use of Solr for searching, faceting and 'more like this' handling.

This guide details the process of installing Solr on Debian-based systems.


Installing Solr
===============

Solr is a java application which needs to run inside a Java servlet container (e.g. Tomcat).
On Debian based system (including Ubuntu) you can install it directly from the apt repository::

    $ apt-get install solr-tomcat

.. _solr-debian-configuring:

Configuring Solr
================

1. Export the solr schema from the project::

    $ ./manage.py build_solr_schema > schema.xml

2. Copy ``schema.xml`` over existing solr ``schema.xml``::

    $ sudo mv schema.xml /etc/solr/conf/schema.xml

3. Enable the ``More Like This`` request handler::

    $ sudo vim /etc/solr/conf/solrconfig.xml

4. Add the following somewhere before the final closing tag::

    <requestHandler name="/mlt" class="org.apache.solr.handler.MoreLikeThisHandler">
        <lst name="defaults">
        <str name="mlt.interestingTerms">list</str>
        </lst>
    </requestHandler>

5. Restart tomcat::

    $ sudo /etc/init.d/tomcat6 restart

6. Rebuild the complete index::

    $ ./manage.py rebuild_index

You can also update the index with::

    $ ./manage.py update_index
