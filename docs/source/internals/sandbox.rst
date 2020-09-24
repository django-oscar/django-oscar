.. spelling::

    uWSGI

=====================
Sample Oscar projects
=====================

Oscar ships with one sample project: a 'sandbox' site, which is a vanilla
install of Oscar using the default templates and styles.

The sandbox site
----------------

The sandbox site is a minimal implementation of Oscar where everything is left
in its default state.  It is useful for exploring Oscar's functionality
and developing new features.

It only has one notable customisation on top of Oscar's core:

* A profile class is specified which defines a few simple fields.  This is to
  demonstrate the account section of Oscar, which introspects the profile class
  to build a combined User and Profile form.

Note that some things are deliberately not implemented within core Oscar as they
are domain-specific.  For instance:

* All tax is set to zero.
* No shipping methods are specified.  The default is free shipping which will
  be automatically selected during checkout (as it's the only option).
* No payment is required to submit an order as part of the checkout process.

The sandbox is, in effect, the blank canvas upon which you can build your site.

Browse the external sandbox site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of the sandbox site is made available at https://latest.oscarcommerce.com

.. warning::

    It is possible for users to access the dashboard and edit the site content.
    Hence, the data can get quite messy.  It is periodically cleaned up.


Run the sandbox locally
~~~~~~~~~~~~~~~~~~~~~~~

It's pretty straightforward to get the sandbox site running locally so you can
play around with Oscar.

In order to compile uWSGI, which is a dependency of the sandbox, you will
first need to install the Python development headers with:::

    $ sudo apt install python3-dev

Install Oscar and its dependencies within a virtualenv:

.. code-block:: bash

    $ git clone https://github.com/django-oscar/django-oscar.git
    $ cd django-oscar
    $ mkvirtualenv --python=python3 oscar  # needs virtualenvwrapper
    (oscar) $ make sandbox
    (oscar) $ sandbox/manage.py runserver

.. warning::

    Note, these instructions will install the head of Oscar's 'master' branch,
    not an official release. Occasionally the sandbox installation process
    breaks while support for a new version of Django is being added (often due
    dependency conflicts with 3rd party libraries). Please ask on the mailing
    list if you have problems.

If you do not have ``mkvirtualenv``, then replace that line with:

.. code-block:: bash

    $ virtualenv --python=python3 oscar
    $ source ./oscar/bin/activate
    (oscar) $

The sandbox site (initialised with a sample set of products) will be available
at: http://localhost:8000.  A sample superuser is installed with credentials::

    username: superuser
    email: superuser@example.com
    password: testing


.. warning::

    The sandbox has Django Debug Toolbar enabled by default, which will affect
    its performance. You can disable it by setting ``INTERNAL_IPS`` to an
    empty list in your local settings.


Run the sandbox using Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run the Oscar sandbox using `Docker`_, run the following commands:

.. _`Docker`: https://www.docker.com/

.. code-block:: bash

    $ docker pull oscarcommerce/django-oscar-sandbox
    $ docker run -p 8080:8080/tcp oscarcommerce/django-oscar-sandbox:latest
