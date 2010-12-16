# Oscar - Ecommerce on Django

Named after Oscar Peterson (http://en.wikipedia.org/wiki/Oscar_Peterson), oscar is a Django implementation
of Taoshop (a product from Tangent Labs).  It's fairly experimental at the moment.

## Installation
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

## Aims of project
* To be a portable Django application that provides ecommerce functionality.  
* To comprise a set of loosely coupled apps that can be overridden in projects (interdependence is on interfaces only)
* To allow core objects (eg products, orders) to be extended within a specific project
