# Django-Oscar - Flexible e-commerce on Django

Named after [Oscar Peterson](http://en.wikipedia.org/wiki/Oscar_Peterson),
django-oscar is a flexible ecommerce platform, structured to allow accurate
domain models to be constructed.  It is not supposed to be a framework that can
be downloaded and fully set up by simply adjusting a configuration file: there will always
be some developer work required to make sure the models match those from your
domain - this is the nature of domain modelling.

However, a small amount of work up front in determine the right models for your
shop can really pay off in terms of building a high-quality application that
is a pleasure to work with and maintain.


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

## Core design decisions

The central aim of django-oscar is to be a flexible app, that can be customised (rather than 
configured) to suit the domain at hand.  This is acheived in several ways:

* **All core models are abstract.**  In each sub-app, there is an `abstract_models.py` file which
defines abstract super-classes for every core model.  There is also an accompanying `models.py` file which provides
a vanilla concrete implementation of each model.  The apps are structured this way so that
any model can be subclassed and extended.  You would do this by creating an app in your project with
the same top-level app label as the one you want to modify (eg `myshop.product` to modify `oscar.product`).
You can then create a models.py file which imports from the corresponding abstract models file but
your concrete implementations can add new fields and methods.  For example, in a clothes shop, you might
want your core `product.Item` model to support fields for `Label`.  

* **Little use of the [Entity-Attribute-Value](http://en.wikipedia.org/wiki/Entity-attribute-value_model) pattern**. 
This technique of subclassing and extending
models avoids an over-reliance on the using the EAV pattern which is commonly used to store data and meta-data about 
domain objects.  

* **Classes are loaded generically.**  To enable sub-apps to be overridden, oscar classes are loading generically
using a special `import_module` function.  This looks at the `INSTALLED_APPS` tuple to determine the appropriate
app to load a class from.

* **All core views are class-based.**  This enables any view to be subclassed and extended within your project.

* **Any template can be overridden by a local version**  This is a simple technique relying on the fact
that the template loader can be configured to look in your project first for oscar templates.


## Installation

Create new django project
    django-admin startproject myshop

Create a new virtual env
    mkvirtualenv --not-site-packages myshop

A nice extension now is to edit your `~/.virtualenv/myshop/bin/postactivate` file to contain
    cd ~/path/to/myshop
so that you can simply type `workon myshop` to jump into your project folder with the virtual
environment set-up.

Install django-oscar using pip 
    pip install -e git+git://github.com/codeinthehole/django-oscar.git#egg=django-oscar

Install the dependencies of oscar [need to fill this part in]

Make the following changes to your `settings.py`:

* Add `'django.middleware.transaction.TransactionMiddleware'` to your `MIDDLEWARE_CLASSES` tuple, making 
  sure it comes BEFORE `'django.contrib.auth.middleware.AuthenticationMiddleware'`.
* Uncomment `django.contrib.admin` from `INSTALLED_APPS`

Add the following to your `INSTALLED_APPS`:
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
    
Now fill in the normal settings (not related to django-oscar) within `settings.py` - eg `DATABASES`, `TIME_ZONE` etc    

### Modelling your domain

Now configure your models.


### Create database

Final step is to create your database schema:
    ./manage.py syncdb


### Stock validation

You can enfore stock validation rules using signals.  You just need to register a listener to 
the BasketLine pre_save signal that checks the line is valid. For example:

    @receiver(pre_save, sender=Line)
    def handle_line_save(sender, **kwargs):
        if 'instance' in kwargs:
            quantity = int(kwargs['instance'].quantity)
            if quantity > 4:
                raise InvalidBasketLineError("You are only allowed to purchase a maximum of 4 of these")

## Installation for django-oscar developers

Set up `virtualenv` if you haven't already done so:
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
	workon oscar
    
After checking out your fork, install the latest version of Django (currenty a beta of 1.3)

    wget http://www.djangoproject.com/download/1.3-beta-1/tarball/
	pip install Django-1.3-beta-1.tar.gz

Install all packages from the requirements file

	pip install -r requirements.txt

Install oscar in development mode within your virtual env

    python setup.py develop

Now create a `local_settings.py` file which contains details of your local database
that you want to use for development.  Be sure to create two databases: one for development
and one for running the unit tests (prefix `test_` on the normal db name).

### Developing

Developing oscar normally involves working on a django project which uses oscar
as a installed app.  There are several such projects within the `examples` folder - the 
`defaultshop` project does not customise oscar at all and uses everything in its 
default format.

Each example shop has its own `manage.py` executable which you can use to create 
your database:

    ./manage.py syncdb
	
There is a shortcut script for dropping all of a projects's apps and rerunning `syncdb` in
the `examples` folder - you need to specify which project to act on:

    ./recreate_project_tables.sh defaultshop
    
There is a similar script for running tests:

    ./run_tests.sh defaultshop
    
This specifies a sqlite3 database to use for testing and filters out the useless output.
    
You can also use the functionality from [django-test-extensions](https://github.com/garethr/django-test-extensions/) which 
is one of the installed app	

Look in the TODO file for things to hack on...
    
### Conventions
* URLs use hyphens not underscores

