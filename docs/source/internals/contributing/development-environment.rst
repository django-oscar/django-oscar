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

The :doc:`sandbox </internals/sandbox>` site can be used to examine changes
locally.  It is easily created by running::

    $ make sandbox

JPEG Support
------------

On Ubuntu, you need to install a few libraries to get JPEG support with
Pillow::

    $ sudo apt-get install python-dev libjpeg-dev libfreetype6-dev zlib1g-dev

If you already installed PIL (you did if you ran ``make install`` previously),
reinstall it::

    $ pip uninstall Pillow
    $ pip install Pillow

Creating migrations
-------------------

As the sandbox is a vanilla Oscar site, it is what we use to build migrations
against::

    $ make sandbox
    $ sites/sandbox/manage.py schemamigration $YOURAPP --auto
    
Writing LESS/CSS
----------------

Oscar's CSS files are built using LESS_.  However, the sandbox defaults to
serving CSS files directly, bypassing LESS compilation.

.. _LESS: http://lesscss.org/

If you want to develop the LESS files, set::

    USE_LESS = True

in ``sites/sandbox/settings_local.py``.  This will include the on-the-fly
``less`` pre-processor. That will allow you to see changes to the LESS
files after a page reload.

You can manually compile the CSS files by running::

    make css

For this to work, you will need to ensure that the pre-processor binary
``lessc`` is installed. Using npm, install LESS using::

    npm install less

.. warning::

    If you do submit a pull request that changes the LESS files.  Please also
    recompile the CSS files and include them in your pull request.

Testing migrations against MySQL and Postgres
---------------------------------------------

To test the migrations against MySQL and Postgres you will need to set
up an environment with both installed and do the following:

1. Change to sandbox folder and activate your virtualenv

2. Run helper script::

    ./test_migrations.sh

    This will recreate the Oscar database in both MySQL and Postgres and rebuild
    it using ``migrate``.
