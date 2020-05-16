======================================
Setting up the development environment
======================================

Fork the repository and run::

    $ git clone git@github.com:<username>/django-oscar.git
    $ cd django-oscar
    $ mkvirtualenv oscar  # needs virtualenvwrapper
    $ make install

If using Ubuntu, the ``python3-dev`` package is required for some packages to
compile.

The :doc:`sandbox </internals/sandbox>` site can be used to examine changes
locally.  It is easily created by running::

    $ make sandbox

JPEG Support
------------

On Ubuntu, you need to install a few libraries to get JPEG support with
Pillow::

    $ sudo apt-get install python3-dev libjpeg-dev libfreetype6-dev zlib1g-dev

If you already installed PIL (you did if you ran ``make install`` previously),
reinstall it::

    $ pip uninstall Pillow
    $ pip install Pillow

Creating migrations
-------------------

As the sandbox is a vanilla Oscar site, it is what we use to build migrations
against::

    $ make sandbox
    $ sandbox/manage.py makemigrations

Writing LESS/CSS
----------------

Oscar's CSS files are built using LESS_.  However, the sandbox defaults to
serving CSS files directly, bypassing LESS compilation.

.. _LESS: http://lesscss.org/

If you want to develop the LESS files, set::

    OSCAR_USE_LESS = True

in ``sandbox/settings_local.py``.  This will include the on-the-fly
``less`` pre-processor. That will allow you to see changes to the LESS
files after a page reload.

You can manually compile static assets files by running::

    npm run build

For this to work, you will need to ensure that the pre-processor binary
``lessc`` is installed. Using npm_, install LESS using::

    npm install less

.. warning::

    If you do submit a pull request that changes the LESS files.  Please also
    recompile the CSS files and include them in your pull request.


.. _npm: https://www.npmjs.com/

Testing migrations against MySQL and PostgreSQL
-----------------------------------------------

To test the migrations against MySQL and PostgreSQL you will need to set
up an environment with both installed and do the following:

1. Change to sandbox folder and activate your virtualenv

2. Run helper script::

    ./test_migrations.sh

This will recreate the Oscar database in both MySQL and PostgreSQL and rebuild
it using ``migrate``.
