======================
Playing in the sandbox
======================

Oscar ships with a 'sandbox' site, which is a vanilla install of Oscar using the
default templates and styles.  It is useful for exploring Oscar's functionality
and developing new features.

It only has two customisations on top of Oscar's core:

* Two shipping methods are specified so that the shipping method step of
  checkout is not skipped.  If there is only one shipping method (which is true of core
  Oscar) then the shipping method step is skipped as there is no choice to be
  made.

* A profile class is specified which defines a few simple fields.  This is to
  demonstrate the account section of Oscar, which introspects the profile class
  to build a combined User and Profile form.

Note that some things are deliberately not implemented within core Oscar as they
are domain-specific.  For instance:

* All tax is set to zero
* No shipping methods are specified.  The default is free shipping.
* No payment is required to submit an order as part of the checkout process

The sandbox is, in effect, the blank canvas upon which you can build your site.

Browse the external sandbox site
================================

An instance of the sandbox site is build hourly from master branch and made
available at http://latest.oscarcommerce.com 

.. warning::
    
    It is possible for users to access the dashboard and edit the site content.
    Hence, the data can get quite messy.  It is periodically cleaned up.

.. warning::
    
    Since this site is built from the unstable branch, occasionally things won't
    be fully stable.  A more stable 'demo' site is in preparation, which will be
    more suitable for impressing clients/management.

Running the sandbox locally
===========================

It's pretty straightforward to get the sandbox site running locally so you can
play around with the source code.

Install Oscar and its dependencies within a virtualenv::

    $ git clone git@github.com:tangentlabs/django-oscar.git
    $ cd django-oscar
    $ mkvirtualenv oscar
    $ make sandbox
    $ sites/sandbox/manage.py runserver

The sandbox site (initialised with a sample set of products) will be available
at: http://localhost:8000.  A sample superuser is installed with credentials::

    username: superuser
    email: superuser@example.com
    password: testing

