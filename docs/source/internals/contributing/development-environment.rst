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

Writing SCSS/CSS
----------------

Oscar's CSS files are built using SASS.

If you want to develop the SCSS files, run::

    npm run watch

Which will watch for and compile changes to the source files into output CSS.

You can manually compile static assets files by running::

    npm run build

Testing migrations
------------------

To test the migrations against PostgreSQL you will need to set
up an environment with both installed and do the following:

1. Change to sandbox folder and activate your virtualenv

2. Run helper script::

    ./test_migrations.sh

This will recreate the Oscar database in PostgreSQL and rebuild it using ``migrate``.
