================================
Installing Oscar for development
================================

Note that these instructions assume you are developing on Ubuntu.

Virtual environment
-------------------

Set up ``pip`` and ``virtualenv`` if you haven't already done so::

    sudo apt-get install python-setuptools
    sudo easy_install pip
    sudo pip install virtualenv virtualenvwrapper
    echo "source `which virtualenvwrapper`" >> ~/.bashrc

Reload bash to add the virtualenvwrapper commands to your path::

    . ~/.bashrc

Create a virtualenv for development::

    mkvirtualenv --no-site-packages oscar
    workon oscar

Forking Oscar
-------------

Sign in to GitHub, navigate to https://github.com/tangentlabs/django-oscar and click "Fork".  This will create a 
copy of the repository in your account.

Now clone the remote repository to your machine::

    cd workspace
    git clone git@github.com:username/django-oscar.git
    
See the GitHub guide to forking for more details (http://help.github.com/fork-a-repo/).      

Install Oscar and dependencies
------------------------------

Install Django and the packages from the requirements file, which aren't essential but are useful
for testing and development::

    pip install Django
    pip install -r requirements-dev.txt

Install Oscar in development mode within your virtualenv::

    cd django-oscar
    python setup.py develop

Note: In case of gcc crashing and complaining in-between installation process,
make sure you have appropriate ``-devel`` packages installed (i.e., ``mysql-devel``) in
your system.

Now create a ``settings_local.py`` file which contains details of your local database
that you want to use for development.  At a minimum, this needs to define the ``DATABASES`` tuple.

Developing
----------

Developing Oscar normally involves working on a Django project which uses Oscar
as a installed app.  There are several such projects within the ``examples`` folder:

* The ``vanilla`` project does not customise Oscar at all and uses everything in its 
  default format.  It represents a blank canvas for an e-commerce shop.
* The ``demo`` project does customise Oscar, and is intended to demonstrate the range 
  of features in Oscar.   

Each example shop has its own ``manage.py`` executable which you can use to create 
your database::

    ./manage.py syncdb
 
Install sample data
-------------------

Oscar ships with sample data for a simple bookshop.  Load the product data and images using the
following commands::

    cd examples/vanilla
    ./manage.py import_catalogue ../sample-data/books.csv
    ./manage.py import_images ../sample-data/book-images/
    ./manage.py update_index 
 
 
Helper scripts
-------------- 
    
There is a shortcut script for dropping all of a projects's apps and rerunning ``syncdb`` in
the `examples` folder - you need to specify which project to act on::

    ./recreate_project_tables.sh vanilla
    
There is a similar script for running tests::

    ./run_tests.sh vanilla
    
This specifies a sqlite3 database to use for testing and filters out the useless output.

