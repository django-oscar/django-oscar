============
Installation
============

For clarity, this installation walk-through assumes you are building a new Oscar
project from scratch.  Let's call this shop 'frobshop'.

.. tip::

    You can always review the set-up of the
    :doc:`Sandbox site <sandbox>` in case you have trouble with
    the below instructions.

Project set-up
--------------

Create a virtualenv and install Oscar (which will install Django as a
dependency):

.. code-block:: bash

    $ mkvirtualenv oscar  # requires virtualenvwrapper
    (oscar) $ pip install django-oscar

.. attention::

    Please ensure that ``pillow``, a fork of the the Python Imaging Library
    (PIL), gets installed with JPEG support. Supported formats are printed
    when ``pillow`` is first installed.

    Instructions_ on how to get JPEG support are highly platform specific,
    but guides for ``PIL`` should work for ``pillow`` as well. Generally
    speaking, you need to ensure that ``libjpeg-dev`` is installed and found
    during installation.

    .. _Instructions: http://www.google.com/search?q=install+pil+with+jpeg+support
    (oscar) $ django-admin.py startproject frobshop

Now create the project folder structure:

.. code-block:: bash

    (oscar) $ django-admin.py startproject frobshop

.. tip::

   You might be interested in the `templated Django project`_ that Tangent uses
   internally. This can be used to create the initial project structure of a new
   Oscar site. The template project comes with test infrastructure[M q2[M#q2

   .. _templated Django project: https://github.com/tangentlabs/tangent-django-boilerplate

Settings
--------

There are a number of settings that need to be specified for Oscar to work
correctly.

``INSTALLED_APPS``
~~~~~~~~~~~~~~~~~~

Modify ``INSTALLED_APPS`` to be a list, add ``South`` and ``compressor``
and append Oscar's core apps:

.. code-block:: python

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

    # A site ID is required for django.contrib.sites
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

.. _django-compressor: https://github.com/django-compressor/django-compressor

Middleware
~~~~~~~~~~

Add ``oscar.apps.basket.middleware.BasketMiddleware`` and
``django.contrib.flatpages.middleware.FlatpageFallbackMiddleware`` to
your ``MIDDLEWARE_CLASSES`` setting. If you're running on Django 1.5, it is
also recommended to use ``django.middleware.transaction.TransactionMiddleware``:

.. code-block:: python

    MIDDLEWARE_CLASSES = (
        ...
        'oscar.apps.basket.middleware.BasketMiddleware',
        'django.middleware.transaction.TransactionMiddleware',  # Django 1.5 only
        'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    )

If you're running Django 1.6 or above, you should enable ``ATOMIC_REQUESTS``
instead (see database settings above).
   
Auth backends
~~~~~~~~~~~~~

Oscar provides a custom auth backend that lets customers authenticate using
their email address and a password. Enable this by setting:

.. code-block:: python

    AUTHENTICATION_BACKENDS = (
        'oscar.apps.customer.auth_backends.EmailBackend',
        'django.contrib.auth.backends.ModelBackend',
    )

Database
~~~~~~~~

Complete your ``DATABASES`` setting. We recommend using ``ATOMIC_REQUESTS`` to
tie transactions to requests (Django 1.6+). Example using Sqlite3:

.. code-block:: python

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

Statics
~~~~~~~

Ensure that your media and static files are `configured correctly`_. This means
at the least setting ``MEDIA_URL`` and ``STATIC_URL``. If you're serving files
locally, you'll also need to set ``MEDIA_ROOT`` and ``STATIC_ROOT``.

Check out the `sandbox settings`_ for a working example. If you're serving
files from a remote storage (e.g. Amazon S3), you must manually copy a
:ref:`"Image not found" image <missing-image-label>` into ``MEDIA_ROOT``.

.. _`configured correctly`: https://docs.djangoproject.com/en/1.7/howto/static-files/
.. _sandbox settings:
   https://github.com/tangentlabs/django-oscar/blob/3a5160a86c9b14c940c76a224a28cd37dd29f7f1/sites/sandbox/settings.py#L99T

Search backends
~~~~~~~~~~~~~~~

If you're happy with basic search for now, you can just use Haystack's simple
backend:

.. code-block:: python

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        },
    }

Oscar uses Haystack_ to provide a clean search API but with a strong preference
for Apache Solr as the production backend. Example production Haystack setting:

.. code-block:: python

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
            'URL': 'http://127.0.0.1:8983/solr',
            'INCLUDE_SPELLING': True,
        },
    }

Oscar includes a sample schema to get started with Solr. More information can be
found in the 
:doc:`recipe on getting Solr up and running</topics/search/how_to_setup_solr>`.

`See how this is configured in the sandbox site`__

__ https://github.com/tangentlabs/django-oscar/search?q=HAYSTACK_CONNECTIONS+path%3Asites%2Fsandbox&type=Code

Template loading
~~~~~~~~~~~~~~~~

Modify your ``TEMPLATE_DIRS`` to include the main Oscar template directory:

.. code-block:: python

    from oscar import OSCAR_MAIN_TEMPLATE_DIR
    TEMPLATE_DIRS = (
        location('templates'),
        OSCAR_MAIN_TEMPLATE_DIR,
    )

Template context processors
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit your settings file ``frobshop.frobshop.settings.py`` to specify
``TEMPLATE_CONTEXT_PROCESSORS``:

.. code-block:: python

    TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.request",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        "django.core.context_processors.static",
        "django.core.context_processors.tz",
        "django.contrib.messages.context_processors.messages",

        # Oscar context processors
        'oscar.apps.search.context_processors.search_form',
        'oscar.apps.promotions.context_processors.promotions',
        'oscar.apps.checkout.context_processors.checkout',
        'oscar.apps.customer.notifications.context_processors.notifications',
        'oscar.core.context_processors.metadata',
    )



Oscar-specific settings
~~~~~~~~~~~~~~~~~~~~~~~

The last addition to the settings file is to import all of Oscar's default
settings:

.. code-block:: python

    from oscar.defaults import *

As you develop your project, you may want to add more Oscar-specific settings.
See the :doc:`settings documentation </ref/settings/` for further information
about what settings are available.

URL routing
-----------

Alter your ``frobshop/urls.py`` to include Oscar's URLs. If you have more than
one language set your Django settings for ``LANGUAGES``, you will also need to
include Django's i18n URLs:

.. code-block:: python

    from django.conf.urls import include, url
    from oscar.app import application

    urlpatterns = [
        url(r'^i18n/', include('django.conf.urls.i18n')),
        url(r'', include(application.urls))
    ]

Create database
---------------

Create an initial version of your database:

.. code-block:: bash

    $ python manage.py syncdb --noinput
    $ python manage.py migrate

and then running:

.. code-block:: bash

    $ python manage.py runserver

should provide an empty, but running Oscar install that you can browse.

Congratulations - Oscar is now installed!

Next steps
----------

Now that vanilla Oscar is running, the next step is to learn about the
techniques available for customising Oscar.
