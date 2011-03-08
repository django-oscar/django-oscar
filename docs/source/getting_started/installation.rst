Installing django-oscar
=======================

Environment
-----------

Install pip and virtualenv (if you haven't already)::

    sudo apt-get install python-setuptools
    sudo easy_install pip
    sudo pip install virtualenv virtualenvwrapper
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc

Create a new django project (this assume you have a version of django installed in your global site-packages)::

    cd /path/to/my/workspace
    django-admin startproject myshop

Create a new virtual env::

    mkvirtualenv --not-site-packages myshop

A nice extension now is to edit your ``~/.virtualenv/myshop/bin/postactivate`` file to contain::

    cd ~/path/to/myshop
    
so that you can simply type ``workon myshop`` to jump into your project folder with the virtual
environment set-up.

Install ``django-oscar``
------------------------

Install django-oscar using pip::
 
    pip install -e git+git://github.com/codeinthehole/django-oscar.git#egg=django-oscar

Make the following changes to your ``settings.py``:

Configure settings
------------------

* Add ``'django.middleware.transaction.TransactionMiddleware'`` to your ``MIDDLEWARE_CLASSES`` tuple, making 
  sure it comes BEFORE ``'django.contrib.auth.middleware.AuthenticationMiddleware'``.
* Uncomment ``django.contrib.admin`` from ``INSTALLED_APPS``

Add the following to your `INSTALLED_APPS`::

    'oscar',
    'oscar.order',
    'oscar.checkout',
    'oscar.order_management',
    'oscar.product',
    'oscar.basket',
    'oscar.payment',
    'oscar.offer',
    'oscar.address',
    'oscar.stock',
    'oscar.image',
    'oscar.shipping',
    'oscar.customer',
    
Now fill in the normal settings (not related to django-oscar) within ``settings.py`` - eg ``DATABASES``, ``TIME_ZONE`` etc    

A vanilla install of django-oscar is now ready, you could now finish the process by running::

    ./manage.py syncdb

However, in reality you will need to start extending the models to match your domain.  It's best to do
this before creating your initial schema.