# Oscar - Flexible e-commerce on Django

Named after Oscar Peterson (http://en.wikipedia.org/wiki/Oscar_Peterson), oscar is a Django implementation
of Taoshop (a product from Tangent Labs).  It's fairly experimental at the moment.  It aims to be
a flexible ecommerce application, built

## Aims of project

* To be a portable Django application that provides ecommerce functionality.  
* To comprise a set of loosely coupled apps that can be overridden in projects (interdependence is on interfaces only)
* To allow core objects (eg products, orders) to be extended within a specific project

The central aim is to provide a solid core of an ecommerce project that can be
extended and customised to suit the domain at hand.  One way to acheive this is
to have enormous models that have fields for every possible variation; however,
this is unwieldy and ugly.  A more elegant solution is to have models where all
the fields are meaningful within the ecommerce domain.  In general, this means
more work up front in terms of creating the right set of models but leads
ultimately to a much cleaner and coherent system.

## Installation for developers
	sudo apt-get install python-setuptools
	sudo easy_install pip
	sudo pip install virtualenv virtualenvwrapper
	echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc

Reload bash with the following command:
    ~/.bashrc

Do the following from your workspace folder:
    mkdir oscar
	cd oscar
    mkvirtualenv --no-site-packages oscar
    
After checking out your fork, install all dependencies:
	workon oscar
	pip install -r requirements.txt

Create a `local_settings.py` file which contains details of your local database
that you want to use for development.  Be sure to create two databases: one for development
and one for running the unit tests (prefix `test_` on the normal db name).
	
## Developing

The database can be created in the normal way
    ./manage.py syncdb
    
There is a shortcut script for dropping all of oscar's apps and rerunning `syncdb`
    ./reset_oscar_tables.sh
    
Run tests using:
    ./manage.py test oscar
    
You can also use the functionality from (https://github.com/garethr/django-test-extensions/) which 
is one of the installed app	
    


