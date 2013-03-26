============================
Start building your own shop
============================

For simplicity, let's assume you're building a new e-commerce project from
scratch and have decided to use Oscar.  Let's call this shop 'frobshop'

.. tip::

    You can always review the set-up of the `Sandbox site`_ in case you have
    trouble with the below instructions.

.. _`Sandbox site`: https://github.com/tangentlabs/django-oscar/tree/master/sites/sandbox

Install by hand
===============

Install Oscar (which will install Django as a dependency), then create the
project:

.. code-block:: bash

    pip install django-oscar
    django-admin.py startproject frobshop

This will create a folder ``frobshop`` for your project.

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

Then, add ``oscar.apps.basket.middleware.BasketMiddleware`` to
``MIDDLEWARE_CLASSES``.  It is also recommended to use
``django.middleware.transaction.TransactionMiddleware`` too

Now set ``TEMPLATE_CONTEXT_PROCESSORS`` to:

.. code-block:: django

    TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.request",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        "django.core.context_processors.static",
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
        'django.contrib.flatpages',
        ...
        'south',
        'compressor',
    ] + get_core_apps()

Note that Oscar requires ``django.contrib.messages`` and
``django.contrib.flatpages`` which aren't included by default.

Next, add ``django.contrib.flatpages.middleware.FlatpageFallbackMiddleware`` to
your ``MIDDLEWARE_CLASSES`` setting:

.. code-block:: django

    MIDDLEWARE_CLASSES = (
        ...
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

Modify your ``TEMPLATE_DIRS`` to include the main Oscar template directory:

.. code-block:: django

    from oscar import OSCAR_MAIN_TEMPLATE_DIR
    TEMPLATE_DIRS = TEMPLATE_DIRS + (OSCAR_MAIN_TEMPLATE_DIR,)

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
        (r'', include(application.urls))
    )

Database
--------

Then create the database and the shop should be browsable:

.. code-block:: bash

    python manage.py syncdb --noinput
    python manage.py migrate

You should now have a running Oscar install that you can browse.

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
Oscar.  The fun part.
