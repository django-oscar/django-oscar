============================
How to setup Solr with Oscar
============================

`Apache Solr`_ is Oscar's recommended production-grade search backend. This
how-to describes how to get Solr running, and integrated with Oscar. The
instructions below are tested on an Ubuntu machine, but should be applicable
for similar environments. A working Java or OpenJDK installation are necessary.

.. _`Apache Solr`: https://lucene.apache.org/solr/

Installing Solr
===============

You first need to fetch and extract Solr. The schema included with Oscar
is tested with Solr 4.7.2:

.. code-block:: bash

    $ wget http://archive.apache.org/dist/lucene/solr/4.7.2/solr-4.7.2.tgz
    $ tar xzf solr-4.7.2.tgz
    
Integrating with Haystack
=========================

Haystack provides an abstraction layer on top of different search backends and
integrates with Django. Your Haystack connection settings in your
``settings.py`` for the config above should look like this:

.. code-block:: python

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
            'URL': 'http://127.0.0.1:8983/solr',
            'INCLUDE_SPELLING': True,
        },
    }

Build solr schema
=================

Next, replace the example configuration with Oscar's.

.. code-block:: bash

    $ ./manage.py build_solr_schema > solr-4.7.2/example/solr/collection1/conf/schema.xml

You should then be able to start Solr by running:

.. code-block:: bash

    $ cd solr-4.7.2/example
    $ java -jar start.jar

Rebuild search index
====================

If all is well, you should now be able to rebuild the search index.

.. code-block:: bash

    $ ./manage.py rebuild_index --noinput
    Removing all documents from your index because you said so.
    All documents removed.
    Indexing 201 Products
    Indexing 201 Products

The products being indexed twice is caused by a low-priority bug in Oscar and
can be safely ignored.  If the indexing succeeded, search in Oscar will be
working. Search for any term in the search box on your Oscar site, and you
should get results.
