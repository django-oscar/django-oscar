======================================
Setting up the development environment
======================================

Fork the repo and run::

    $ git clone git@github.com:<username>/django-oscar.git
    $ cd django-oscar
    $ mkvirtualenv oscar  # needs virtualenvwrapper
    $ make install

If using Ubuntu, the ``python-dev`` package is required for some packages to
compile.

The :doc:`sandbox </internals/sandbox>` site can be used to test our changes in
a browser. It is easily created with ``make sandbox``.

JPEG Support
------------

On Ubuntu, you need to install a few libraries to get JPEG support with Pillow.

    $ sudo apt-get install python-dev libjpeg-dev libfreetype6-dev zlib1g-dev

If you did already install PIL (you did if you ran ``make install`` previously),
reinstall it:

    $ pip uninstall Pillow
    $ pip install Pillow

Creating migrations
===================

As the sandbox is a vanilla Oscar site, it is what we use to build migrations
against::

    $ make sandbox
    $ sites/sandbox/manage.py schemamigration $YOURAPP --auto
    
Writing LESS/CSS
================

Oscar's CSS files are build using LESS_.  However, the sandbox defaults to
serving CSS files directly, bypassing LESS compilation.

.. _LESS: http://lesscss.org/

If you want to develop the LESS files, set::

    USE_LESS = True
    COMPRESS_ENABLED = False

in ``sites/sandbox/settings_local.py``.  This will cause Oscar to use
`django-compressor`_ to compile the LESS files as they are requested.  For this to
work, you will need to ensure that the LESS compiler ``lessc`` is installed.
This can be acheived by running::

    pip install -r requirements_less.txt

.. _`django-compressor`: http://django_compressor.readthedocs.org/en/latest/

which will install the `virtual-node`_ and `virtual-less`_ packages, which will
install node.js and LESS in your virtualenv.  

.. _`virtual-node`: https://github.com/elbaschid/virtual-node
.. _`virtual-less`: https://github.com/elbaschid/virtual-less

If you have npm installed already,
you install LESS using::

    npm install less

You can manually compile the CSS files by running::

    make css

.. warning::

    If you do submit a pull request that changes the LESS files.  Please also
    recompile the CSS files and include them in your pull request.

Vagrant
=======

Oscar ships with a Vagrant_ virtual machine that can be used to test integration
with various services in a controlled environment.  For instance, it is used to
test that the migrations run correctly in both MySQL and Postgres.

.. _Vagrant: http://vagrantup.com/

Building the Vagrant machine
----------------------------

To create the machine, first ensure that Vagrant and puppet_ are installed.  You will require a
puppet version that supports ``puppet module install``, that is > 2.7.14.  Now
run::

    make puppet

.. _puppet: http://docs.puppetlabs.com/guides/installation.html

to fetch the required puppet modules for provisioning.  Finally, run::

    vagrant up

to create the virtual machine and provision it.

Testing migrations against MySQL and Postgres
---------------------------------------------

To test the migrations against MySQL and Postgres, do the following:

1. SSH onto the VM::

    vagrant ssh

2. Change to sandbox folder and activate virtualenv::

    cd /vagrant/sites/sandbox
    source /var/www/virtualenv/bin/activate

3. Run helper script::

    ./test_migrations.sh

    This will recreate the Oscar database in both MySQL and Postgres and rebuild
    it using ``syncdb`` and ``migrate``.

Testing WSGI server configurations
----------------------------------

You can browse the Oscar sandbox site with different deployment setups. Just
open up http://localhost:808x on your host machine.

* Django's development server runs on port 8080.

* The Vagrant machine runs Apache2 and mod_wsgi on port 8081.

* Nginx acts as a reverse proxy to Apache on port 8082.

* Nginx acts as a reverse proxy to gunicorn on port 8083.

