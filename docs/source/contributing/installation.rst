Installing django-oscar for development
=======================================

Set up `virtualenv` if you haven't already done so::

    sudo apt-get install python-setuptools
    sudo easy_install pip
    sudo pip install virtualenv virtualenvwrapper
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc

Note: Fedora (and possibly other Red Hat based distros) installs virtualenvwrapper.sh in /usr/bin path, so the last line above should read::

    echo "source /usr/bin/virtualenvwrapper.sh" >> ~/.bashrc

Reload bash with the following command::

    ~/.bashrc

Do the following from your workspace folder::

    mkdir oscar
    cd oscar
    mkvirtualenv --no-site-packages oscar
    workon oscar
    
After checking out your fork, install the latest version of Django into your virtualenv (currenty a beta of 1.3)::

    pip install django

Install all packages from the requirements file (optional)::

    pip install -r requirements-dev.txt

This just provides some useful tooling for developing a django project - the installed
modules are not mandatory to run oscar.

Install oscar in development mode within your virtual env::

    python setup.py develop

Note: In case of gcc crashing and complaining in-between installation process,
make sure you have appropriate -devel packages installed (ie. mysql-devel) in
your system.

Now create a `local_settings.py` file which contains details of your local database
that you want to use for development.  Be sure to create two databases: one for development
and one for running the unit tests (prefix `test_` on the normal db name).

Install sample data
-------------------

Oscar ships with sample data for a simple bookshop.  Load the product data and images using the
following commands::

    cd examples/vanilla
    ./manage.py import_catalogue ../sample-data/books.csv
    ./manage.py import_images ../sample-data/book-images/
    ./manage.py update_index


Developing
----------

Developing oscar normally involves working on a django project which uses oscar
as a installed app.  There are several such projects within the `examples` folder - the 
`defaultshop` project does not customise oscar at all and uses everything in its 
default format.

Each example shop has its own `manage.py` executable which you can use to create 
your database::

    ./manage.py syncdb
    
There is a shortcut script for dropping all of a projects's apps and rerunning `syncdb` in
the `examples` folder - you need to specify which project to act on::

    ./recreate_project_tables.sh defaultshop
    
There is a similar script for running tests::

    ./run_tests.sh defaultshop
    
This specifies a sqlite3 database to use for testing and filters out the useless output.

