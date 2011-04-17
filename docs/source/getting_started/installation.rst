=======================
Installing django-oscar
=======================

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
    
Install oscar and its dependencies::    
    
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
  sure it comes BEFORE ``'django.contrib.auth.middleware.AuthenticationMiddleware'``.
  
* Uncomment ``django.contrib.admin`` from ``INSTALLED_APPS``.

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

Configure URLs
--------------

Oscar comes with a number of urls and views out of the box.  These are
recommendations rather than a requirement but you easily use them in your
e-commerce site by adding the oscar urls to your projects local ``urls.py``::

    (r'^', include('oscar.urls')),

This will bring in all of oscar's defined urls. Of course you can pull in the
urls for the individual apps if you prefer or simply define your own