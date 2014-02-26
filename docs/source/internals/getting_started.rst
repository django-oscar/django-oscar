======================
Building your own shop
======================

For simplicity, let's assume you're building a new e-commerce project from
scratch and have decided to use Oscar.  Let's call this shop 'frobshop'

.. tip::

    You can always review the set-up of the
    :doc:`Sandbox site <sandbox>` in case you have trouble with
    the below instructions.

Install by hand
===============

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

Settings
--------

Now edit your settings file ``frobshop.frobshop.settings.py`` to specify a
database (we use SQLite for simplicity):

.. code-block:: django

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        }
    }

Now set ``TEMPLATE_CONTEXT_PROCESSORS`` to:

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

Next, add ``oscar.apps.basket.middleware.BasketMiddleware``, 
``django.contrib.flatpages.middleware.FlatpageFallbackMiddleware`` to
your ``MIDDLEWARE_CLASSES`` setting. It is also recommended to use
``django.middleware.transaction.TransactionMiddleware``:

.. code-block:: django

    MIDDLEWARE_CLASSES = (
        ...
        'oscar.apps.basket.middleware.BasketMiddleware',
        'django.middleware.transaction.TransactionMiddleware',  # recommended for oscar
        'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    )

More info about `django-flatpages installation`_ at the django-project website.

.. _`django-flatpages installation`: https://docs.djangoproject.com/en/dev/ref/contrib/flatpages/#installation

.. tip::

    Oscar's default templates use django-compressor_ but it's optional really.
    You may decide to use your own templates that don't use compressor.  Hence
    why it is not one of the 'core apps'.

.. _django-compressor: https://github.com/jezdez/django_compressor

Now set your auth backends to:

.. code-block:: django

    AUTHENTICATION_BACKENDS = (
        'oscar.apps.customer.auth_backends.Emailbackend',
        'django.contrib.auth.backends.ModelBackend',
    )

to allow customers to sign in using an email address rather than a username.

Set ``MEDIA_ROOT`` and ``MEDIA_URL`` to your environment, and make sure the
path in ``MEDIA_ROOT`` exists. An example from the Sandbox site:

.. code-block:: django


    PROJECT_DIR = os.path.dirname(__file__)
    location = lambda x: os.path.join(
        os.path.dirname(os.path.realpath(__file__)), x)
    MEDIA_ROOT = location("public/media")
    MEDIA_URL = '/media/'

Verify your ``staticfiles`` settings and ensure that files in ``MEDIA_ROOT``
get served:

* `staticfiles in Django 1.3 and 1.4 <https://docs.djangoproject.com/en/1.3/howto/static-files/#serving-other-directories>`_
* `staticfiles in Django 1.5 <https://docs.djangoproject.com/en/1.5/howto/static-files/#serving-files-uploaded-by-a-user>`_

Modify your ``TEMPLATE_DIRS`` to include the main Oscar template directory:

.. code-block:: django

    from oscar import OSCAR_MAIN_TEMPLATE_DIR
    TEMPLATE_DIRS = (
        location('templates'),
        OSCAR_MAIN_TEMPLATE_DIR,
    )

Oscar currently uses Haystack for search so you need to specify:

.. code-block:: django

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        },
    }

When moving towards production, you'll obviously need to switch to a real search
backend.

The last addition to the settings file is to import all of Oscar's default settings:

.. code-block:: django

    from oscar.defaults import *

URLs
----

Alter your ``frobshop/urls.py`` to include Oscar's URLs:

.. code-block:: django

    from django.conf.urls import patterns, include, url
    from oscar.app import application

    urlpatterns = patterns('',
        url(r'', include(application.urls))
    )

Database
--------

Then create the database and the shop should be browsable:

.. code-block:: bash

    $ python manage.py syncdb --noinput
    $ python manage.py migrate
    $ python manage.py runserver

You should now have a running Oscar install that you can browse.

Fixtures
--------

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
-------------------------------------------------

Every Oscar deployment needs at least one
:class:`product class <oscar.apps.catalogue.abstract_models.AbstractProductClass>`
and one
:class:`fulfillment partner <oscar.apps.partner.abstract_models.AbstractPartner>`.
These aren't created automatically as they're highly specific to the shop you
want to build.
The quickest way to set them up is to log into the Django admin
interface at http://127.0.0.1:8000/admin/ and create instances of both there.
For a deployment setup, we recommend creating them as `data migration`_.

.. _data migration: http://codeinthehole.com/writing/prefer-data-migrations-to-initial-data/

Defining the order pipeline
---------------------------

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
