# These targets are not files
.PHONY: contribute ci test i18n lint travis

install:
	python setup.py develop
	pip install -r requirements.txt

sandbox: install
	[ -f sites/sandbox/db.sqlite ] && rm sites/sandbox/db.sqlite || true
	# Create database
	sites/sandbox/manage.py syncdb --noinput
	sites/sandbox/manage.py migrate
	# Import some fixtures
	sites/sandbox/manage.py oscar_import_catalogue sites/_fixtures/books-catalogue.csv
	sites/sandbox/manage.py oscar_import_catalogue_images sites/_fixtures/books-images.tar.gz
	sites/sandbox/manage.py loaddata countries.json sites/_fixtures/pages.json sites/_fixtures/auth.json
	sites/sandbox/manage.py rebuild_index --noinput

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
	../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=da; \
	../sites/sandbox/manage.py makemessages --ignore=sandbox/ --locale=sk
