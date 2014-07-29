# These targets are not files
.PHONY: install sandbox geoip demo docs coverage lint travis messages compiledmessages puppet css clean preflight

install:
	pip install -r requirements.txt
	python setup.py develop

sandbox: install
	# Remove media
	-rm -rf sites/sandbox/public/media/images
	-rm -rf sites/sandbox/public/media/cache
	-rm -rf sites/sandbox/public/static
	-rm -f sites/sandbox/db.sqlite
	# Create database
	# 'syncdb' is identical to migrate in Django 1.7+; but calling it twice should have no effect
	sites/sandbox/manage.py syncdb --noinput
	sites/sandbox/manage.py migrate
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	sites/sandbox/manage.py loaddata sites/sandbox/fixtures/child_products.json
	sites/sandbox/manage.py oscar_import_catalogue sites/sandbox/fixtures/*.csv
	sites/sandbox/manage.py oscar_import_catalogue_images sites/sandbox/fixtures/images.tar.gz
	sites/sandbox/manage.py oscar_populate_countries
	sites/sandbox/manage.py loaddata sites/_fixtures/pages.json sites/_fixtures/auth.json sites/_fixtures/ranges.json sites/_fixtures/offers.json
	sites/sandbox/manage.py clear_index --noinput
	sites/sandbox/manage.py update_index catalogue

geoip:
	wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
	gunzip GeoLiteCity.dat.gz
	mv GeoLiteCity.dat sites/demo/geoip

demo: install
	# Install additional requirements
	pip install -r requirements_demo.txt
	# Create database
	# Breaks on Travis because of https://github.com/django-extensions/django-extensions/issues/489
	if [ -z "$(TRAVIS)" ]; then sites/demo/manage.py reset_db --router=default --noinput; fi
	sites/demo/manage.py syncdb --noinput
	sites/demo/manage.py migrate
	# Import some core fixtures
	sites/demo/manage.py oscar_populate_countries
	sites/demo/manage.py loaddata sites/_fixtures/pages.json
	# Create catalogue (create product classes from fixture than import CSV files)
	sites/demo/manage.py loaddata sites/_fixtures/auth.json sites/demo/fixtures/offers.json
	sites/demo/manage.py loaddata sites/demo/fixtures/product-classes.json sites/demo/fixtures/product-attributes.json sites/demo/fixtures/shipping-event-types.json
	sites/demo/manage.py create_demo_products --class=Books sites/demo/fixtures/books.csv
	sites/demo/manage.py create_demo_products --class=Downloads sites/demo/fixtures/downloads.csv
	sites/demo/manage.py create_demo_products --class=Clothing sites/demo/fixtures/clothing.csv
	sites/demo/manage.py oscar_import_catalogue_images sites/demo/fixtures/images.tar.gz
	# Update search index
	sites/demo/manage.py clear_index --noinput
	sites/demo/manage.py update_index catalogue

us_site: install
	# Install additional requirements
	pip install -r requirements_us.txt
	# Create database
	sites/us/manage.py reset_db --router=default --noinput
	sites/us/manage.py syncdb --noinput
	sites/us/manage.py migrate
	# Import some fixtures
	sites/us/manage.py oscar_populate_countries
	sites/us/manage.py loaddata sites/us/fixtures/*.json
	sites/us/manage.py loaddata sites/_fixtures/auth.json sites/_fixtures/ranges.json 
	# Create catalogue (using a fixture from the demo site)
	sites/us/manage.py create_demo_products --class=Books sites/demo/fixtures/books.csv

docs:
	cd docs && make html

coverage:
	coverage run ./runtests.py --with-xunit
	coverage xml -i

lint:
	./lint.sh

testmigrations:
	pip install -r requirements_vagrant.txt
	cd sites/sandbox && ./test_migrations.sh

# It is important that this target only depends on install
# (instead of upgrade) because we install Django in the .travis.yml
# and upgrade would overwrite it.  We also build the sandbox as part of this target
# to catch any errors that might come from that build process.
travis: install lint coverage sandbox demo testmigrations

messages:
	# Create the .po files used for i18n
	cd oscar; django-admin.py makemessages -a

compiledmessages:
	# Compile the gettext files
	cd oscar; django-admin.py compilemessages

puppet:
	# Install puppet modules required to set-up a Vagrant box
	mkdir -p sites/puppet/modules
	rm -rf sites/puppet/modules/*
	puppet module install --target-dir sites/puppet/modules/ saz-memcached -v 2.0.2
	puppet module install --target-dir sites/puppet/modules/ puppetlabs/mysql
	puppet module install --target-dir sites/puppet/modules/ puppetlabs/apache
	puppet module install --target-dir sites/puppet/modules/ dhutty/nginx
	git clone git://github.com/akumria/puppet-postgresql.git sites/puppet/modules/postgresql
	git clone git://github.com/puppetmodules/puppet-module-python.git sites/puppet/modules/python
	git clone git://github.com/codeinthehole/puppet-userconfig.git sites/puppet/modules/userconfig

css:
	# Compile CSS files from LESS
	lessc oscar/static/oscar/less/styles.less > oscar/static/oscar/css/styles.css
	lessc oscar/static/oscar/less/responsive.less > oscar/static/oscar/css/responsive.css
	lessc oscar/static/oscar/less/dashboard.less > oscar/static/oscar/css/dashboard.css
	# Compile CSS for demo site
	lessc sites/demo/static/demo/less/styles.less > sites/demo/static/demo/css/styles.css
	lessc sites/demo/static/demo/less/responsive.less > sites/demo/static/demo/css/responsive.css

clean:
	# Remove files not in source control
	find . -type f -name "*.pyc" -delete
	rm -rf nosetests.xml coverage.xml htmlcov *.egg-info *.pdf dist violations.txt

preflight: lint
    # Bare minimum of tests to run before pushing to master
	./runtests.py

todo:
	# Look for areas of the code that need updating when some event has taken place (like 
	# Oscar dropping support for a Django version)
	-grep -rnH TODO *.txt
	-grep -rnH TODO oscar/apps/
	-grep -rnH "django.VERSION" oscar/apps
