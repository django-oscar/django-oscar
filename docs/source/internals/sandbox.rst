======================
Playing in the sandbox
======================

Browse the sandbox site
=======================

There is a demo Oscar site built hourly from HEAD of the master branch (unstable):
http://latest.oscarcommerce.com

It is intended to be a vanilla install of Oscar, using the default templates and
styles.  This is the blank canvas upon which you an build your application.

It only has two customisations on top of Oscar's core:

* Two shipping methods are specified so that the shipping method step of
  checkout is not skipped.  If there is only one shipping method (which is true of core
  Oscar) then the shipping method step is skipped as there is no choice to be
  made.

* A profile class is specified which defines a few simple fields.  This is to
  demonstrate the account section of Oscar, which introspects the profile class
  to build a combined User and Profile form.

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

Note that some things are deliberately not implemented within core Oscar
as they are domain-specific.  For instance:

* All tax is set to zero
* The two shipping methods are both free
* No payment is required to submit an order
