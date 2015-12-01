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

An instance of the sandbox site is built hourly from master branch and made
available at http://latest.oscarcommerce.com 

.. warning::
    
    It is possible for users to access the dashboard and edit the site content.
    Hence, the data can get quite messy.  It is periodically cleaned up.


Run the sandbox locally
~~~~~~~~~~~~~~~~~~~~~~~

It's pretty straightforward to get the sandbox site running locally so you can
play around with Oscar.

.. warning::
    
    While installing Oscar is straightforward, some of Oscar's dependencies
    don't support Windows and are tricky to be properly installed, and therefore
    you might encounter some errors that prevent a successful installation.
    
Install Oscar and its dependencies within a virtualenv:

.. code-block:: bash

    $ git clone https://github.com/django-oscar/django-oscar.git
    $ cd django-oscar
    $ mkvirtualenv oscar  # needs virtualenvwrapper
    (oscar) $ make sandbox
    (oscar) $ sites/sandbox/manage.py runserver

.. warning::
    
    Note, these instructions will install the head of Oscar's 'master' branch,
    not an official release. Occasionally the sandbox installation process
    breaks while support for a new version of Django is being added (often due
    dependency conflicts with 3rd party libraries). Please ask on the mailing
    list if you have problems.

If you do not have ``mkvirtualenv``, then replace that line with:

.. code-block:: bash

    $ virtualenv oscar
    $ source ./oscar/bin/activate
    (oscar) $

The sandbox site (initialised with a sample set of products) will be available
at: http://localhost:8000.  A sample superuser is installed with credentials::

    username: superuser
    email: superuser@example.com
    password: testing
