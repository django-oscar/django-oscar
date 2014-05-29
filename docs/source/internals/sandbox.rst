=====================
Sample Oscar projects
=====================

Oscar ships with three sample projects: a 'sandbox' site, which is a vanilla
install of Oscar using the default templates and styles, a sample US site which
customises Oscar to use US style taxes, and a fully featured
'demo' site which demonstrates how Oscar can be re-skinned and customised to
model a domain.

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

An instance of the sandbox site is build hourly from master branch and made
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

    $ git clone https://github.com/tangentlabs/django-oscar.git
    $ cd django-oscar
    $ mkvirtualenv oscar  # needs virtualenvwrapper
    (oscar) $ make sandbox
    (oscar) $ sites/sandbox/manage.py runserver

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

.. _us_site:

The US site
-----------

The US site is a relatively simple Oscar that makes a few key customisations in
order to mimic how sites in the US work. Specifically, it:

- Overrides the partner app to supply a new strategy selector which ensures all
  prices are return without taxes.

- Overrides the checkout app in order to apply taxes to submissions once the
  shipping address is known.

To browse the US site locally run:

.. code-block:: bash

   (oscar) $ make us_site
   (oscar) $ sites/us/manage.py runserver

and the US site will be browsable at http://localhost:8000

The demo site
-------------

The demo site is *the* reference Oscar project as it illustrates how Oscar can
be redesigned and customised to build an realistic e-commerce store. The demo
site is a sailing store selling a range of different product types.

The customisations on top of core Oscar include:

* A new skin
* A variety of product types including books, clothing and downloads
* Payment with PayPal Express using django-oscar-paypal_.
* Payment with bankcards using Datacash using django-oscar-datacash_.

.. _django-oscar-paypal: https://github.com/tangentlabs/django-oscar-paypal
.. _django-oscar-datacash: https://github.com/tangentlabs/django-oscar-datacash

.. note::

    Both the sandbox and demo site have the Django admin interface wired up.
    This is done as a convenience for developers to browse the model instances.

    Having said that, the Django admin interface is *unsupported* and will fail
    or be of little use for some models. At the time of writing, editing
    products in the admin is clunky and slow, and editing categories is
    not supported at all.

Browse the external demo site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An instance of the demo site is built periodically (but not automatically) and
available at http://demo.oscarcommerce.com. It is typically updated when new
versions of Oscar are released.

Run the demo site locally
~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming you've already set-up the sandbox site, there are two further services
required to run the demo site:

* A spatially aware database such as PostGIS.  The demo site uses
  django-oscar-stores_ which requires a spatial capabilities for store searching.

* A search backend that supports faceting such as Solr.  You should use the
  sample schema file from ``sites/demo/deploy/solr/schema.xml``.

Once you have set up these services, create a local settings file from a template
to house your credentials:

.. code-block:: bash
    
    (oscar) $ cp sites/demo/settings_local{.sample,}.py
    (oscar) $ vim sites/demo/settings_local.py  # Add DB creds

Now build the demo site:

.. code-block:: bash

    (oscar) $ make demo
    (oscar) $ sites/demo/manage.py runserver

The demo (initialised with a sample set of products) will be available
at: http://localhost:8000.

.. _django-oscar-stores: https://github.com/tangentlabs/django-oscar-stores
