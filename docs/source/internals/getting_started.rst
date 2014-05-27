======================
Building your own shop
======================

For simplicity, let's assume you're building a new e-commerce project from
scratch and have decided to use Oscar.  Let's call this shop 'frobshop'

.. tip::

    You can always review the set-up of the
    :doc:`Sandbox site <sandbox>` in case you have trouble with
    the below instructions.

Install Oscar and its dependencies
==================================

Install Oscar (which will install Django as a dependency), then create the
project:

.. code-block:: bash

    $ mkvirtualenv oscar
    $ pip install django-oscar
    $ django-admin.py startproject frobshop

If you do not have mkvirtualenv, then replace that line with::

    $ virtualenv oscar
    $ . ./oscar/bin/activate
    (oscar) $

This will create a folder ``frobshop`` for your project. It is highly
recommended to install Oscar in a virtualenv.

.. attention::

    Please ensure that ``pillow``, a fork of the the Python Imaging Library
    (PIL), gets installed with JPEG support. Supported formats are printed
    when ``pillow`` is first installed.
    Instructions_ on how to get JPEG support are highly platform specific,
    but guides for ``PIL`` should work for ``pillow`` as well. Generally
    speaking, you need to ensure that ``libjpeg-dev`` is installed and found
    during installation.

    .. _Instructions: http://www.google.com/search?q=install+pil+with+jpeg+support

Django settings
===============

Edit your settings file ``frobshop.frobshop.settings.py`` to specify
``TEMPLATE_CONTEXT_PROCESSORS``:

.. code-block:: django

    TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.request",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        "django.core.context_processors.static",
        "django.core.context_processors.tz",
        "django.contrib.messages.context_processors.messages",
        'oscar.apps.search.context_processors.search_form',
        'oscar.apps.promotions.context_processors.promotions',
        'oscar.apps.checkout.context_processors.checkout',
        'oscar.apps.customer.notifications.context_processors.notifications',
        'oscar.core.context_processors.metadata',
    )

Next, modify ``INSTALLED_APPS`` to be a list, add ``South`` and ``compressor``
and append Oscar's core apps:

.. code-block:: django

    from oscar import get_core_apps

    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.flatpages',
        ...
        'south',
        'compressor',
    ] + get_core_apps()

    SITE_ID = 1

Note that Oscar requires ``django.contrib.flatpages`` which isn't
included by default. ``flatpages`` also requires ``django.contrib.sites``,
which won't be enabled by default when using Django 1.6 or upwards.
More info about installing ``flatpages`` is in the `Django docs`_.

.. _`Django docs`: https://docs.djangoproject.com/en/dev/ref/contrib/flatpages/#installation

.. tip::

    Oscar's default templates use django-compressor_ but it's optional really.
    You may decide to use your own templates that don't use compressor.  Hence
    why it is not one of the 'core apps'.

.. _django-compressor: https://github.com/jezdez/django_compressor

Next, add ``oscar.apps.basket.middleware.BasketMiddleware`` and
``django.contrib.flatpages.middleware.FlatpageFallbackMiddleware`` to
your ``MIDDLEWARE_CLASSES`` setting. If you're running on Django 1.5, it is
also recommended to use ``django.middleware.transaction.TransactionMiddleware``:

.. code-block:: django

    MIDDLEWARE_CLASSES = (
        ...
        'oscar.apps.basket.middleware.BasketMiddleware',
        'django.middleware.transaction.TransactionMiddleware',  # Django 1.5 only
        'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    )

If you're running Django 1.6 or above, you should enable ``ATOMIC_REQUESTS``
instead (see database settings above).

Set your auth backends to:

.. code-block:: django

    AUTHENTICATION_BACKENDS = (
        'oscar.apps.customer.auth_backends.EmailBackend',
        'django.contrib.auth.backends.ModelBackend',
    )

to allow customers to sign in using an email address rather than a username.

Ensure that your media and static files are `configured correctly`_. This means
at the least setting ``MEDIA_URL`` and ``STATIC_URL``. If you're serving files
locally, you'll also need to set ``MEDIA_ROOT`` and ``STATIC_ROOT``.
Check out the `sandbox settings`_ for a working example. If you're serving
files from a remote storage (e.g. Amazon S3), you must manually copy a
:ref:`"Image not found" image <missing-image-label>` into ``MEDIA_ROOT``.

.. _`configured correctly`: https://docs.djangoproject.com/en/1.7/howto/static-files/
.. _sandbox settings: https://github.com/tangentlabs/django-oscar/blob/3a5160a86c9b14c940c76a224a28cd37dd29f7f1/sites/sandbox/settings.py#L99

Modify your ``TEMPLATE_DIRS`` to include the main Oscar template directory:

.. code-block:: django

    from oscar import OSCAR_MAIN_TEMPLATE_DIR
    TEMPLATE_DIRS = (
        location('templates'),
        OSCAR_MAIN_TEMPLATE_DIR,
    )

The last addition to the settings file is to import all of Oscar's default settings:

.. code-block:: django

    from oscar.defaults import *

URLs
====

Alter your ``frobshop/urls.py`` to include Oscar's URLs. If you have more than
one language set your Django settings for ``LANGUAGES``, you will also need to
include Django's i18n URLs:

.. code-block:: django

    from django.conf.urls import include, url
    from oscar.app import application

    urlpatterns = [
        url(r'^i18n/', include('django.conf.urls.i18n')),
        url(r'', include(application.urls))
    ]

Search backend
==============
If you're happy with basic search for now, you can just use Haystack's simple
backend:

.. code-block:: django

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        },
    }

Oscar uses Haystack to abstract away from different search backends.
Unfortunately, writing backend-agnostic code is nonetheless hard and
Apache Solr is currently the only supported production-grade backend. Your
Haystack config could look something like this:

.. code-block:: django

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
            'URL': 'http://127.0.0.1:8983/solr',
            'INCLUDE_SPELLING': True,
        },
    }

Oscar includes a sample schema to get started with Solr. More information can
be found in the
:doc:`recipe on getting Solr up and running</howto/how_to_setup_solr>`.

Database
========

Check your database settings. A quick way to get started is to use SQLite:

.. code-block:: django

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
            'ATOMIC_REQUESTS': True,  # Django 1.6+
        }
    }

Note that we recommend using ``ATOMIC_REQUESTS`` to tie transactions to
requests.

Then create the database and the shop should be browsable:

.. code-block:: bash

    $ python manage.py syncdb --noinput
    $ python manage.py migrate
    $ python manage.py runserver

You should now have an empty, but running Oscar install that you can browse at
http://localhost:8000.

Fixtures
========

The default checkout process requires a shipping address with a country.  Oscar
uses a model for countries with flags that indicate which are valid shipping
countries and so the ``address_country`` database table must be populated before
a customer can check out.

This is easily achieved using fixtures.  Oscar ships with a ``countries.json``
fixture that loads most countries from the `ISO 3166 standard`_.  This can loaded
via::

    $ python manage.py loaddata countries

Note however that this file only sets the UK as a valid shipping country.  If
you want other countries to be available, it would make more sense to take a
copy of Oscar's countries fixture and edit it as you see it before loading it.

Further, a simple way of loading countries for your project is to use a `data
migration`_.

.. _`ISO 3166 standard`: http://en.wikipedia.org/wiki/ISO_3166
.. _`data migration`: http://codeinthehole.com/writing/prefer-data-migrations-to-initial-data/


Creating product classes and fulfillment partners
=================================================

Every Oscar deployment needs at least one
:class:`product class <oscar.apps.catalogue.abstract_models.AbstractProductClass>`
and one
:class:`fulfillment partner <oscar.apps.partner.abstract_models.AbstractPartner>`.
These aren't created automatically as they're highly specific to the shop you
want to build.
The quickest way to set them up is to log into the Django admin
interface at http://127.0.0.1:8000/admin/ and create instances of both there.
For a deployment setup, we recommend creating them as `data migration`_.

Defining the order pipeline
===========================

The order management in Oscar relies on the order pipeline that
defines all the statuses an order can have and the possible transitions
for any given status. Statuses in Oscar are not just used for an order
but are handled on the line level as well to be able to handle partial
shipping of an order.

The order status pipeline is different for every shop which means that
changing it is fairly straightforward in Oscar. The pipeline is defined in
your ``settings.py`` file using the ``OSCAR_ORDER_STATUS_PIPELINE`` setting.
You also need to specify the initial status for an order and a line item in
``OSCAR_INITIAL_ORDER_STATUS`` and ``OSCAR_INITIAL_LINE_STATUS``
respectively.

To give you an idea of what an order pipeline might look like take a look
at the Oscar sandbox settings:

.. code-block:: django

    OSCAR_INITIAL_ORDER_STATUS = 'Pending'
    OSCAR_INITIAL_LINE_STATUS = 'Pending'
    OSCAR_ORDER_STATUS_PIPELINE = {
        'Pending': ('Being processed', 'Cancelled',),
        'Being processed': ('Processed', 'Cancelled',),
        'Cancelled': (),
    }

Defining the order status pipeline is simply a dictionary of where each
status is given as a key. Possible transitions into other statuses can be
specified as an iterable of status names. An empty iterable defines an
end point in the pipeline.

With these three settings defined in your project you'll be able to see
the different statuses in the order management dashboard.

Next steps
==========

The next step is to implement the business logic of your domain on top of
Oscar. The fun part.
