# These targets are not files
.PHONY: install sandbox geoip demo docs coverage lint travis messages compiledmessages css clean preflight make_sandbox make_demo

install:
	pip install -e . -r requirements.txt

build_sandbox:
	# Remove media
	-rm -rf sites/sandbox/public/media/images
	-rm -rf sites/sandbox/public/media/cache
	-rm -rf sites/sandbox/public/static
	-rm -f sites/sandbox/db.sqlite
	# Create database
	sites/sandbox/manage.py migrate
	# Import some fixtures. Order is important as JSON fixtures include primary keys
	sites/sandbox/manage.py loaddata sites/sandbox/fixtures/child_products.json
	sites/sandbox/manage.py oscar_import_catalogue sites/sandbox/fixtures/*.csv
	sites/sandbox/manage.py oscar_import_catalogue_images sites/sandbox/fixtures/images.tar.gz
	sites/sandbox/manage.py oscar_populate_countries
	sites/sandbox/manage.py loaddata sites/_fixtures/pages.json sites/_fixtures/auth.json sites/_fixtures/ranges.json sites/_fixtures/offers.json
	sites/sandbox/manage.py loaddata sites/sandbox/fixtures/orders.json
	sites/sandbox/manage.py clear_index --noinput
	sites/sandbox/manage.py update_index catalogue

sandbox: install build_sandbox

geoip:
	wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
	gunzip GeoLiteCity.dat.gz
	mv GeoLiteCity.dat sites/demo/geoip

build_demo:
	# Install additional requirements
	pip install -r requirements_demo.txt
	# Create database
	# Breaks on Travis because of https://github.com/django-extensions/django-extensions/issues/489
	if [ -z "$(TRAVIS)" ]; then sites/demo/manage.py reset_db --router=default --noinput; fi
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

demo: install build_demo

us_site: install
	# Install additional requirements
	pip install -r requirements_us.txt
	# Create database
	sites/us/manage.py reset_db --router=default --noinput
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
	pip install -r requirements_migrations.txt
	cd sites/sandbox && ./test_migrations.sh

# This target is run on Travis.ci. We lint, test and build the sandbox/demo
# sites as well as testing migrations apply correctly. We don't call 'install'
# first as that is run as a separate part of the Travis build process.
travis: coverage lint build_sandbox build_demo testmigrations

messages:
	# Create the .po files used for i18n
	cd src/oscar; django-admin.py makemessages -a

compiledmessages:
	# Compile the gettext files
	cd src/oscar; django-admin.py compilemessages

css:
	# Compile CSS files from LESS
	lessc --source-map --source-map-less-inline src/oscar/static/oscar/less/styles.less src/oscar/static/oscar/css/styles.css
	lessc --source-map --source-map-less-inline src/oscar/static/oscar/less/dashboard.less src/oscar/static/oscar/css/dashboard.css
	# Compile CSS for demo site
	lessc --source-map --source-map-less-inline sites/demo/static/demo/less/styles.less sites/demo/static/demo/css/styles.css
	lessc --source-map --source-map-less-inline sites/demo/static/demo/less/responsive.less sites/demo/static/demo/css/responsive.css

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
	-grep -rnH TODO src/oscar/apps/
	-grep -rnH "django.VERSION" src/oscar/apps
