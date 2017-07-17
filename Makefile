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
	sites/sandbox/manage.py migrate

sandbox: install build_sandbox

geoip:
	wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
	gunzip GeoLiteCity.dat.gz
	mv GeoLiteCity.dat sites/demo/geoip

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
travis: lint coverage build_sandbox build_demo testmigrations

messages:
	# Create the .po files used for i18n
	cd src/oscar; django-admin.py makemessages -a

compiledmessages:
	# Compile the gettext files
	cd src/oscar; django-admin.py compilemessages

css:
	# Compile CSS files from LESS
	lessc --source-map --source-map-less-inline src/oscar/static/oscar/less/styles.less src/oscar/static/oscar/css/styles.css
	lessc --source-map --source-map-less-inline src/oscar/static/oscar/less/responsive.less src/oscar/static/oscar/css/responsive.css
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
