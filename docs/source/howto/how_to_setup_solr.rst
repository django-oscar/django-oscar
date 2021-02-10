.. spelling::

    Solr

============================
How to setup Solr with Oscar
============================

`Apache Solr`_ is Oscar's recommended production-grade search backend. This
how-to describes how to get Solr running, and integrated with Oscar. The
instructions below are tested on an Debian/Ubuntu machine, but should be applicable
for similar environments. A working Java or OpenJDK version 8 installation are
necessary.

.. _`Apache Solr`: https://lucene.apache.org/solr/

Python Package
==============

You will need to install the ``pysolr`` Python package. Or add it to your
`requirements.txt`:

.. code-block:: bash

    $ pip install pysolr

Installing Solr
===============

You first need to fetch and extract Solr. The schema included with Oscar
is tested with Solr 6.6.6:

.. code-block:: bash

    $ wget -O ${HOME}/solr-6.6.6.tgz https://archive.apache.org/dist/lucene/solr/6.6.6/solr-6.6.6.tgz
    $ tar xzf ${HOME}/solr-6.6.6.tgz --directory=${HOME}
    $ ln -s ${HOME}/solr-6.6.6 ${HOME}/solr

.. note::
    For development this will presume the solr directory is in
    the users ``HOME`` directory. (For an actual deployment this may be better
    placed in ``/opt``).

Start Solr and Create a Core
======================================

Next start up Solr and create a core named ``sandbox`` this name will be used
through out this howto, change ``sandbox`` to something that suits your installation.
This step also sets up up the directory structure and a basic configuration.

.. code-block:: bash

    $ cd ${HOME}/solr
    $ ./bin/solr start
    $ ./bin/solr create -c sandbox -n basic_config

Integrating with Haystack
=========================

Haystack provides an abstraction layer on top of different search backends and
integrates with Django. The Haystack connection settings in your
``settings.py`` for the config above will look like this:

.. code-block:: python

    # Solr 6.x
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
            'URL': 'http://127.0.0.1:8983/solr/sandbox',
            'ADMIN_URL': 'http://127.0.0.1:8983/solr/admin/cores',
            'INCLUDE_SPELLING': True,
        },
    }

To use Solr with the Sandbox locally comment out the ``HAYSTACK_CONNECTIONS``
section using the WhooshEngine and uncomment the Solr 6.x section like this one.

Build Solr schema
=================

Next, get Oscar to generate the ``schema.xml`` and ``solrconfig.xml`` for Solr.

.. code-block:: bash

    $ ./manage.py build_solr_schema --configure-directory=${HOME}/solr/server/solr/sandbox/conf
    $ ./manage.py build_solr_schema --reload-core sandbox

.. note::
    If using this Solr install with the Sandbox locally ensure the steps up to
    this point have been done prior to running ``make sandbox`` in the
    `Run the sandbox locally <https://django-oscar.readthedocs.io/en/latest/internals/sandbox.html#run-the-sandbox-locally>`_
    instructions.

Rebuild search index
====================

If all is well, you should now be able to rebuild the search index.

.. code-block:: bash

    $ ./manage.py rebuild_index --noinput
    Removing all documents from your index because you said so.
    All documents removed.
    Indexing 201 Products

If the indexing succeeded, search in Oscar will be working. Search for any term
in the search box on your Oscar site, and you should get results.
