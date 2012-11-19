===========
Take a peek
===========

There are several ways to get a feel for Oscar and what it can do.

Browse the sandbox site
=======================

There is a demo Oscar site, built hourly from HEAD of the master branch (unstable):
http://sandbox.oscar.tangentlabs.co.uk

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
play around with the sourcecode.

Install Oscar and its dependencies within a virtualenv::

    git clone git://github.com/tangentlabs/django-oscar.git
    cd django-oscar
    mkvirtualenv oscar
    make sandbox

This will install all dependencies required for developing Oscar and create a
simple database populated with products.

You can then browse a sample Oscar site using Django's development server::

    cd sites/sandbox
    ./manage.py runserver

Note that some things are deliberately not implemented within core Oscar
as they are domain-specific.  For instance:

* All tax is set to zero
* The two shipping methods are both free
* No payment is required to submit an order

I've found a problem!
---------------------

Good for you - please `report them in GitHub's issue tracker`_.

.. _`report them in GitHub's issue tracker`: https://github.com/tangentlabs/django-oscar/issues

Browse some real Oscar implementations
======================================

There are several Oscar implementations in production, although several are B2B
and hence can't be browsed by the public.  Here's a few public ones to have a
look at:

* http://www.landmarkonthenet.com - Landmark is part of Tata Group.  This site
  has a catalogue size of more than 20 million products and integrates with many
  partners such as Gardners, Ingram, Nielsen, Citibank, Qwikcilver and SAP.

* http://www.dolbeau.ca/ - "Dolbeau delivers weekly limited editions of
  handcrafted luxury menswear"
