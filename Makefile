# These targets are not files
.PHONY: contribute ci test i18n lint travis

install:
	python setup.py develop
	pip install -r requirements.txt

sandbox: install
	-rm -f sites/sandbox/db.sqlite
	# Create database
	sites/sandbox/manage.py syncdb --noinput
	sites/sandbox/manage.py migrate
	# Import some fixtures
	sites/sandbox/manage.py oscar_import_catalogue sites/_fixtures/books-catalogue.csv
	sites/sandbox/manage.py oscar_import_catalogue_images sites/_fixtures/books-images.tar.gz
	sites/sandbox/manage.py loaddata countries.json sites/_fixtures/pages.json sites/_fixtures/auth.json
	sites/sandbox/manage.py rebuild_index --noinput

demo: install
	-rm -f sites/demo/db.sqlite
	# Create database
	sites/demo/manage.py syncdb --noinput
	sites/demo/manage.py migrate
	# Import some fixtures
	sites/demo/manage.py oscar_import_catalogue sites/_fixtures/books-catalogue.csv
	sites/demo/manage.py oscar_import_catalogue_images sites/_fixtures/books-images.tar.gz
	sites/demo/manage.py loaddata countries.json sites/_fixtures/pages.json sites/_fixtures/auth.json
	sites/demo/manage.py rebuild_index --noinput

test: 
	./runtests.py tests/

ci: install lint
	# Run continous tests and generate lint reports
	./runtests.py --with-coverage --with-xunit
	coverage xml

lint:
	./lint.sh

travis: install test lint

i18n:
	# Create the .po files used for i18n 
	cd oscar; \
		../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=de; \
		../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=fr; \
		../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=pl; \
		../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=ru; \
		../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=es; \
		../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=it; \
		../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=da

puppet:
	# Install puppet modules required to set-up a Vagrant box
	rm -rf sites/puppet/modules/*
	puppet module install --target-dir sites/puppet/modules/ saz-memcached -v 2.0.2
	puppet module install --target-dir sites/puppet/modules/ puppetlabs/mysql
	puppet module install --target-dir sites/puppet/modules/ puppetlabs/apache
	git clone git://github.com/akumria/puppet-postgresql.git sites/puppet/modules/postgresql
	git clone git://github.com/uggedal/puppet-module-python.git sites/puppet/modules/python
	git clone git://github.com/codeinthehole/puppet-userconfig.git sites/puppet/modules/userconfig
