# These targets are not files
.PHONY: contribute ci test i18n

contribute:
	# Create a sandbox installation for playing around with oscar.
	python setup.py develop
	pip install -r requirements.txt
	# Create database
	sandbox/manage.py syncdb --noinput
	sandbox/manage.py migrate
	# Import some fixtures
	sandbox/manage.py oscar_import_catalogue sandbox/data/books-catalogue.csv
	sandbox/manage.py oscar_import_catalogue_images sandbox/data/books-images.tar.gz
	sandbox/manage.py loaddata countries.json sandbox/fixtures/pages.json

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
		../sandbox/manage.py makemessages --ignore=sandbox/ --locale=de; \
		../sandbox/manage.py makemessages --ignore=sandbox/ --locale=fr; \
		../sandbox/manage.py makemessages --ignore=sandbox/ --locale=pl; \
		../sandbox/manage.py makemessages --ignore=sandbox/ --locale=ru; \
		../sandbox/manage.py makemessages --ignore=sandbox/ --locale=es; \
		../sandbox/manage.py makemessages --ignore=sandbox/ --locale=it; \
		../sandbox/manage.py makemessages --ignore=sandbox/ --locale=da