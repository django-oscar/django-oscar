================
Installing Oscar
================

Environment
-----------

This section is optional but recommended.

Install pip and virtualenv (if you haven't already)::

    sudo apt-get install python-setuptools
    sudo easy_install pip
    sudo pip install virtualenv virtualenvwrapper
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc

Create a new virtual env::

    mkvirtualenv --no-site-packages $PROJECTNAME

A nice extension now is to edit your ``~/.virtualenv/$PROJECTNAME/bin/postactivate`` file to contain::

    cd ~/path/to/my/workspace/$PROJECTNAME

so that you can simply type ``workon $PROJECTNAME`` to jump into your project folder with the virtual
environment set-up.

Installation
------------

Install Oscar and its dependencies::

    pip install -e git+git://github.com/tangentlabs/django-oscar.git#egg=django-oscar

You will also need to install the appropriate python module for your database of choice.
If you are using MySQL, then run the following::

    pip install MySQL-python

Also, depending on your search backend for haystack, you'll need to install further
packages::

    pip install pysolr

Now create the project::

    cd /path/to/my/workspace
    django-admin.py startproject $PROJECTNAME

Configure ``settings.py``
-------------------------

* Add ``'django.middleware.transaction.TransactionMiddleware'`` to your ``MIDDLEWARE_CLASSES`` tuple, making
  sure it comes AFTER ``'django.contrib.auth.middleware.AuthenticationMiddleware'``.

* Add the following to your `INSTALLED_APPS`::

    'haystack',
    'oscar',
    'oscar.apps.analytics',
    'oscar.apps.discount',
    'oscar.apps.order',
    'oscar.apps.checkout',
    'oscar.apps.shipping',
    'oscar.apps.order_management',
    'oscar.apps.product',
    'oscar.apps.basket',
    'oscar.apps.payment',
    'oscar.apps.offer',
    'oscar.apps.address',
    'oscar.apps.partner',
    'oscar.apps.image',
    'oscar.apps.customer',
    'oscar.apps.promotions',
    'oscar.apps.reports',
    'oscar.apps.search',
    'oscar.apps.catalogue_import',


* Add these to ``TEMPLATE_CONTECT_PROCESSORS``::

    'oscar.apps.search.context_processors.search_form',
    'oscar.apps.promotions.context_processors.promotions',
    'oscar.apps.promotions.context_processors.merchandising_blocks',

* Import default settings::

    from oscar.defaults import *

* If using Solr, configure it::

    HAYSTACK_SITECONF = 'oscar.search_sites'
    HAYSTACK_SEARCH_ENGINE = 'solr'
    HAYSTACK_SOLR_URL = 'http://127.0.0.1:8080/solr'
    HAYSTACK_INCLUDE_SPELLING = True

Now fill in the normal settings (not related to Oscar) within ``settings.py`` - e.g., ``DATABASES``, ``TIME_ZONE`` etc

A vanilla install of Oscar is now ready, you could now finish the process by running::

    ./manage.py syncdb

However, in reality you will need to start extending the models to match your domain.  It's best to do
this before creating your initial schema.

Configure URLs
--------------

Oscar comes with a number of urls and views out of the box.  These are
recommendations rather than a requirement, but you easily use them in your
e-commerce site by adding the Oscar urls to your projects local ``urls.py``::

    (r'^', include('oscar.urls')),

This will bring in all of Oscar's defined urls. Of course you can pull in the
urls for the individual apps if you prefer or simply define your own
