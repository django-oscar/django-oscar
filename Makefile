# These targets are not files
.PHONY: install upgrade sandbox demo coverage ci i18n lint travis docs

install:
	pip install -r requirements.txt --use-mirrors
	python setup.py develop

upgrade:
	pip install --upgrade -r requirements.txt --use-mirrors
	python setup.py develop --upgrade

sandbox: install
	-rm -f sites/sandbox/db.sqlite
	# Create database
	sites/sandbox/manage.py syncdb --noinput
	sites/sandbox/manage.py migrate
	# Import some fixtures
	sites/sandbox/manage.py oscar_import_catalogue sites/_fixtures/books-catalogue.csv
	sites/sandbox/manage.py oscar_import_catalogue_images sites/_fixtures/books-images.tar.gz
	sites/sandbox/manage.py loaddata countries.json sites/_fixtures/pages.json sites/_fixtures/auth.json sites/_fixtures/ranges.json sites/_fixtures/offers.json
	sites/sandbox/manage.py rebuild_index --noinput

demo: install
	-rm -f sites/demo/db.sqlite
	# Create database
	sites/demo/manage.py syncdb --noinput
	sites/demo/manage.py migrate
	# Import some fixtures
	sites/demo/manage.py oscar_import_catalogue sites/_fixtures/books-catalogue.csv
	sites/demo/manage.py oscar_import_catalogue_images sites/_fixtures/books-images.tar.gz
	sites/demo/manage.py loaddata countries.json sites/_fixtures/pages.json sites/_fixtures/auth.json sites/_fixtures/ranges.json
	sites/demo/manage.py rebuild_index --noinput

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
	git clone git://github.com/akumria/puppet-postgresql.git sites/puppet/modules/postgresql
	git clone git://github.com/uggedal/puppet-module-python.git sites/puppet/modules/python
	git clone git://github.com/codeinthehole/puppet-userconfig.git sites/puppet/modules/userconfig

css:
	# Compile CSS files from LESS
	lessc oscar/static/oscar/less/styles.less > oscar/static/oscar/css/styles.css
	lessc oscar/static/oscar/less/responsive.less > oscar/static/oscar/css/responsive.css
	lessc oscar/static/oscar/less/dashboard.less > oscar/static/oscar/css/dashboard.css

clean:
	# Remove files not in source control
	find . -type f -name "*.pyc" -delete
	rm -rf nosetests.xml coverage.xml htmlcov *.egg-info *.pdf dist violations.txt
