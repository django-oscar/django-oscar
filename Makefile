# These targets are not files
.PHONY: contribute ci test i18n

contribute:
	# Create a sandbox installation for playing around with oscar.
	python setup.py develop
	pip install -r requirements.txt
	# Create database
	sites/sandbox/manage.py syncdb --noinput
	sites/sandbox/manage.py migrate
	# Import some fixtures
	sites/sandbox/manage.py oscar_import_catalogue sites/sandbox/data/books-catalogue.csv
	sites/sandbox/manage.py oscar_import_catalogue_images sites/sandbox/data/books-images.tar.gz
	sites/sandbox/manage.py loaddata countries.json sites/sandbox/fixtures/pages.json

ci:
	# Run continous tests and generate lint reports
	python setup.py develop
	pip install -r requirements.txt
	./runtests.py --with-coverage --with-xunit
	flake8 oscar | perl -ple "s/: /: [E] /" | grep -v migrations > violations.txt

test:
	./runtests.py

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