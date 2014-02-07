# These targets are not files
.PHONY: install upgrade sandbox demo coverage ci i18n lint travis docs

install:
	pip install -r requirements.txt
	python setup.py develop

upgrade:
	pip install --upgrade -r requirements.txt --use-mirrors
	python setup.py develop --upgrade

sandbox: install
	# Remove media
	-rm -rf sites/sandbox/public/media/images
	-rm -rf sites/sandbox/public/media/cache
	-rm -rf sites/sandbox/public/static
	-rm -f sites/sandbox/db.sqlite
	# Create database
	sites/sandbox/manage.py syncdb --noinput
	sites/sandbox/manage.py migrate
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	sites/sandbox/manage.py loaddata sites/sandbox/fixtures/variants.json
	sites/sandbox/manage.py oscar_import_catalogue sites/sandbox/fixtures/*.csv
	sites/sandbox/manage.py oscar_import_catalogue_images sites/sandbox/fixtures/images.tar.gz
	sites/sandbox/manage.py loaddata countries.json sites/_fixtures/pages.json sites/_fixtures/auth.json sites/_fixtures/ranges.json sites/_fixtures/offers.json
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
	sites/demo/manage.py reset_db --router=default --noinput
	sites/demo/manage.py syncdb --noinput
	sites/demo/manage.py migrate
	# Import some core fixtures
	sites/demo/manage.py loaddata countries.json sites/_fixtures/pages.json
	# Create catalogue (create product classes from fixture than import CSV files)
	sites/demo/manage.py loaddata sites/demo/fixtures/auth.json sites/demo/fixtures/offers.json
	sites/demo/manage.py loaddata sites/demo/fixtures/product-classes.json sites/demo/fixtures/product-attributes.json sites/demo/fixtures/shipping-event-types.json
	sites/demo/manage.py create_products --class=Books sites/demo/fixtures/books.csv
	sites/demo/manage.py create_products --class=Downloads sites/demo/fixtures/downloads.csv
	sites/demo/manage.py create_products --class=Clothing sites/demo/fixtures/clothing.csv
	sites/demo/manage.py oscar_import_catalogue_images sites/demo/fixtures/images.tar.gz
	# Update search index
	sites/demo/manage.py clear_index --noinput
	sites/demo/manage.py update_index catalogue

docs:
	cd docs && make html

coverage:
	coverage run ./runtests.py --with-xunit
	coverage xml -i

# We probably should use upgrade instead of install here but we have a conflict
# around django versions which conflicts with tox.  Use install for now until
# upgrade can run without conflict.
ci: install lint coverage

lint:
	./lint.sh

# It is important that this target only depends on install
# (instead of upgrade) because we install Django in the .travis.yml
# and upgrade would overwrite it.  We also build the sandbox as part of this target
# to catch any errors that might come from that build process.
travis: install lint coverage sandbox
	pip install -r requirements_vagrant.txt
	cd sites/sandbox && ./test_migrations.sh

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

demo_css:
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
